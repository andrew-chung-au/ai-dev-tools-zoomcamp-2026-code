# Table Ready

This document is written for both human contributors and AI coding assistants picking up work in this repo — especially as the project moves into AWS deployment and CI/CD. Read this file first before making changes.

## 1. Project overview

**Table Ready** is a configurable restaurant waitlist and table-management application for independent, table-service venues.

Guests join the queue via a mobile-friendly QR code or link, receive a stable ticket code (`A-001`, `B-002`, ...) and an estimated wait, and can check status from their own device. Staff manage the queue, tables, wait estimates, notifications, seating, cancellations, and no-shows from an authenticated dashboard. The app is built for **one configurable venue per installation** — branding, policies, tables, and messages are configuration, not hard-coded to a specific restaurant.

## 2. Architecture

Table Ready ships as a **single Docker image containing both the frontend and the backend**, deployed alongside a PostgreSQL database. There is no separate frontend server in production.

```
                 ┌──────────────────────────────────────────┐
                 │              app container                │
                 │                                            │
 Browser ───────▶│  FastAPI (uvicorn, :8091)                 │
                 │    • /api/*  → JSON API (routers/*)       │
                 │    • /*      → serves frontend_dist/       │
                 │               (built React SPA, via        │
                 │                StaticFiles + catch-all)    │
                 └───────────────┬────────────────────────────┘
                                  │ SQLAlchemy (psycopg2)
                                  ▼
                 ┌──────────────────────────────────────────┐
                 │           postgres container               │
                 └──────────────────────────────────────────┘
```

**The build (`Dockerfile`) is a two-stage, multi-stage build:**

1. **`frontend-build` stage** (`node:22-slim`) — installs the frontend's npm dependencies, builds the TanStack Start app with `VITE_API_BASE_URL=/api` (same-origin, since the backend will serve it), and renames the prerendered shell to `index.html`. Output: static files in `frontend/.output/public`.
2. **`backend` stage** (`ghcr.io/astral-sh/uv:python3.12-bookworm-slim`) — installs Python deps with `uv sync --frozen --no-dev`, then `COPY --from=frontend-build` copies the built static SPA into `./frontend_dist`. `FRONTEND_DIST_DIR=/app/frontend_dist` tells `backend/main.py` where to find it.

At runtime, `backend/main.py`'s `create_app()` mounts `frontend_dist/assets` as static files and adds a catch-all route: any non-`/api/*` path serves the matching static file if one exists, otherwise falls back to `index.html` (so client-side routing works on a hard refresh/deep link). In local dev, `FRONTEND_DIST_DIR` is unset and the frontend instead runs from its own Vite dev server on port 8080, talking to the backend over CORS.

**Database schema is managed by Alembic, not `create_all()`.** The `docker-compose.yml` stack has a one-shot `migrate` service (`alembic upgrade head`) that runs after `postgres` is healthy; `app` then waits for `migrate` to complete successfully before starting. See §6 (Local Setup) for the commands.

## 3. Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, [TanStack Start](https://tanstack.com/start) + TanStack Router + TanStack Query, Vite, Tailwind CSS, shadcn/radix UI components. Ships as a static SPA (prerendered shell + client hydration) — **no Node server in production.** |
| Backend | Python, FastAPI, SQLAlchemy 2.x (ORM), Alembic (migrations), Uvicorn |
| Database | PostgreSQL 16 (Docker Compose locally; SQLite is also supported for fast local dev/tests via a config-only `DATABASE_URL` swap — see `backend/db.py`) |
| API contract | OpenAPI (`openapi.yaml`) |
| Backend package manager | [`uv`](https://docs.astral.sh/uv/) |
| Frontend package manager | `bun` for local dev/tests; the Docker build uses `npm` instead (Node-only, no Bun in the build image) |
| E2E browser testing | Playwright (`e2e/`, its own npm project) |

## 4. Project structure

```
02-restaurant-waitlist/
├── backend/                    # FastAPI app (Python, uv-managed)
│   ├── main.py                 #   create_app(): CORS, routers, static SPA mount
│   ├── config.py                #   env-driven config: DATABASE_URL, ALLOWED_ORIGINS, FRONTEND_DIST_DIR
│   ├── db.py                    #   SQLAlchemy Base / engine / session factory
│   ├── orm_models.py            #   SQLAlchemy ORM entities (source of truth for schema)
│   ├── models.py                #   Pydantic domain/response models
│   ├── schemas.py               #   Pydantic request schemas
│   ├── repositories.py          #   DatabaseRepository (SQLAlchemy-backed) — what's actually injected at
│   │                              #   runtime (see deps.py); demo data seeding
│   ├── repository.py            #   InMemoryRepository — origin of the repo interface; routers/services
│   │                              #   still type-hint against this class, but only DatabaseRepository is
│   │                              #   ever instantiated today
│   ├── routers/                 #   one module per API resource (auth, venue, tables, waitlist_entries, ...)
│   ├── services/                #   business logic, one module per domain area
│   ├── deps.py, errors.py, security.py, notifications.py, utils.py
│   └── alembic/                 #   ← Alembic migration environment (see §7)
│       ├── env.py               #     reads DATABASE_URL from env; target_metadata = Base.metadata
│       └── versions/            #     migration scripts, one per schema change
├── alembic.ini                  # Alembic config (repo root, alongside pyproject.toml); script_location → backend/alembic
├── frontend/                    # TanStack Start app (bun-managed)
│   ├── src/routes/              #   file-based routes: index, join, login, status.$accessToken, staff.*
│   ├── src/components/, src/services/, src/hooks/, src/lib/
│   └── .env.example              #   VITE_API_BASE_URL, VITE_USE_MOCK_SERVICE
├── tests/                        # Backend pytest suite
│   ├── conftest.py               #   TestClient fixture; creates ephemeral per-test SQLite schema directly
│   │                              #   (Base.metadata.create_all) — deliberately bypasses Alembic for speed
│   ├── test_*.py                 #   fast, in-process API tests (no Docker)
│   └── integration/              #   tests against the *live* docker-compose stack (needs Docker; `integration` marker)
├── e2e/                          # Standalone Playwright project (own package.json, npm-managed)
│   └── tests/                    #   browser tests against the live compose stack (staff + guest sessions)
├── docker-compose.yml            # postgres + migrate (alembic upgrade head) + app, for local prod-like runs and e2e/integration tests
├── Dockerfile                    # multi-stage build described in §2
├── Makefile                      # run / test / e2e targets — see §6
├── openapi.yaml                  # API contract
├── _docs/                        # process, specs, task templates, team-role docs
│   ├── specs.md                  #   full product specification
│   ├── process.md                #   how work is organised (PM/Engineer/QA agent roles, git workflow)
│   └── testing-guidelines.md, design-system.md — referenced by AGENTS.md as required reading before
│                                  #   touching tests / UI, but do not currently exist in the tree; treat
│                                  #   their absence as a gap to flag, not as "nothing to read"
├── _session-summaries/           # per-session engineering handover notes (one file per issue/step)
├── docs/                         # deployment.md, release-process.md, testing.md, ai-usage-report.md,
│                                  #   operations-and-security-report.md — mostly placeholders today, being
│                                  #   filled in as the AWS/CI-CD work lands (see §7)
├── incident-response/, observability/, security-audit/  # placeholders for ops docs, currently empty
└── infra/                        # ⚠ does not exist yet — this is where AWS CloudFormation templates
                                    #   for Staging/Production are expected to land next (see §7)
```

**AGENTS.md / CLAUDE.md** at this directory's root are binding project instructions for AI assistants working here — notably: work only within `02-restaurant-waitlist/`, never `git add .`/`git add -A`, never add a `pyproject.toml` dependency without asking, and read `_docs/testing-guidelines.md` before writing tests.

## 5. Testing strategy

Three layers, each with a different scope and a different way of running:

1. **Backend unit/integration tests — Pytest, `tests/*.py`.** Fast, in-process `TestClient` tests with no Docker: each test gets its own throwaway SQLite file (schema created directly via `Base.metadata.create_all()`, not Alembic — see `tests/conftest.py`). This is the default `uv run pytest` run.
2. **Backend-against-Postgres integration test — Pytest, `tests/integration/*.py`, `integration` marker.** Runs over real HTTP against the `app` container from `docker-compose.yml`, wired to the real `postgres` container, and cross-checks persistence with a direct SQL query — proving data actually lands in Postgres, not just that the API echoes it back. Needs Docker; excluded from the default `pytest` run (`addopts = "-m 'not integration'"` in `pyproject.toml`). Run explicitly with `uv run pytest tests/integration -m integration`.
3. **End-to-end browser tests — Playwright, standalone project in `e2e/`.** A separate npm project (not part of the `frontend/` bun workspace) that drives a real Chromium browser against the live compose stack on `http://localhost:8091`. `e2e/tests/staff-sees-guest-realtime.spec.ts` runs two independent browser sessions — a signed-in staff dashboard and an anonymous guest — and verifies the staff dashboard picks up a new guest join.

   **Important for anyone testing this: the app has no WebSocket/SSE channel.** "Real-time" here means HTTP polling — the staff dashboard's summary counts auto-refresh via TanStack Query's `refetchInterval` (`staff.index.tsx`, every 20s; the guest status page polls every 15s), while the detailed entries list only refetches on an explicit "Refresh" click or staff action. The e2e spec tests exactly this: an unattended poll-driven count increment, followed by a Refresh-triggered row appearing. If a real push channel is ever added, that spec's "click Refresh" step should be revisited.

All three are orchestrated by **`make e2e`**: brings up `docker compose up -d --build` (postgres → migrate → app), polls `http://localhost:8091/api/venue` until the app answers, runs the Playwright suite (`npm install && npx playwright install --with-deps chromium && npm test`), then tears the stack down (`docker compose down`) regardless of pass/fail so it never leaks containers.

## 6. Local setup

**Prerequisites:** `uv`, `bun`, Docker + Docker Compose.

### Fastest path — SQLite, no Docker

```bash
make run              # applies `alembic upgrade head` against a local SQLite file, then starts uvicorn on :8091
cd frontend && bun run dev   # Vite dev server on :8080, proxying API calls to :8091 via CORS
```

Open `http://localhost:8080`.

### Prod-like path — Postgres via Docker Compose

```bash
docker compose up -d --build   # postgres → migrate (alembic upgrade head) → app, all on :8091
```

The `app` container serves both the API and the built frontend from `http://localhost:8091` (single origin — no separate frontend dev server needed here). `docker compose down` to stop; add `-v` to also drop the `postgres-data` volume for a clean-slate rerun.

### Running the test suites

```bash
uv run pytest                              # backend unit tests (fast, no Docker)
uv run pytest tests/integration -m integration   # backend-vs-real-Postgres (needs Docker)
cd frontend && bun test                    # frontend unit tests
make test                                  # frontend + backend unit tests together
make e2e                                   # full compose stack + Playwright e2e suite (needs Docker)
```

### Working with migrations

```bash
# Write a new migration after changing backend/orm_models.py:
uv run alembic revision --autogenerate -m "describe the change"
# Review the generated script in backend/alembic/versions/ before committing — autogenerate is a draft, not gospel.

# Apply migrations locally:
uv run alembic upgrade head             # uses DATABASE_URL from the environment, or the SQLite fallback in alembic.ini
```

`backend/alembic/env.py` sets `target_metadata` from `backend/db.py`'s `Base` (populated by importing `backend/orm_models.py`), and overrides `sqlalchemy.url` from the `DATABASE_URL` environment variable when set — the same variable `backend/config.py` reads for the app itself, so migrations and the app are always pointed at the same database.

## 7. Current state & roadmap

This app started as Module 2 of the AI Dev Tools Zoomcamp coursework and has since been **extracted into its own standalone repository**, primarily to get it off the shared local disk (the original monorepo layout was hitting local disk-space constraints during development). Recent work has taken it from an in-memory/SQLite prototype toward a deployable service:

- ✅ SQLite persistence via SQLAlchemy (database-agnostic from the start — see `backend/db.py`)
- ✅ Containerized, multi-stage Docker build serving the SPA from FastAPI (§2)
- ✅ PostgreSQL via Docker Compose, with integration tests proving real persistence
- ✅ Playwright e2e suite + `make e2e` orchestration
- ✅ Alembic migrations replacing `Base.metadata.create_all()` at startup (`backend/alembic/`, `migrate` service in `docker-compose.yml`)

**Immediate next step: AWS deployment.** The near-term goal is authoring CloudFormation templates for **Staging** and **Production** environments (an `infra/` directory does not exist yet in this repo — that's the next thing to create), plus the CI/CD pipeline to deploy through them. Anyone (human or AI) picking this up should expect to:

- Decide how the single Docker image (§2) maps onto AWS compute (ECS/Fargate is the natural fit given the existing container-first design; no infra code exists yet to confirm this).
- Replace the local Compose Postgres with a managed RDS instance per environment, and point `DATABASE_URL` at it — the app and Alembic already only depend on that one environment variable, by design.
- Wire `alembic upgrade head` into the deploy pipeline the same way `docker-compose.yml`'s `migrate` service does locally (run-once-before-app-starts), rather than inventing a new pattern.
- Check `docs/deployment.md`, `docs/release-process.md`, and `_docs/process.md` — several are currently near-empty placeholders being filled in as this work lands, but are the intended home for deployment/runbook documentation going forward.
