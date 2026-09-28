# Issue #5 — Step 7: Dockerfile serving a static frontend build

Covers only the "multi-stage Dockerfile + backend serves static frontend"
slice of issue #5 ("Table Ready Deployment: Step 1 — Containerize and
migrate to Postgres via Docker Compose"). Postgres, `docker-compose.yml`,
integration tests, and Playwright E2E tests from that issue are **not**
done — see Follow-ups.

## What changed

- `Dockerfile` (new) — two stages:
  - `frontend-build` (`node:22-slim`): `npm install`, `npm run build` with
    `VITE_API_BASE_URL=/api` baked in (same-origin, host/port independent),
    then renames the generated `.output/public/_shell.html` to
    `index.html`.
  - `backend` (`ghcr.io/astral-sh/uv:python3.12-bookworm-slim`): `uv sync
    --frozen --no-dev`, copies the frontend stage's `.output/public` into
    `./frontend_dist`, sets `FRONTEND_DIST_DIR=/app/frontend_dist`, runs
    `uv run uvicorn backend.main:app --host 0.0.0.0 --port 8091`.
- `frontend/vite.config.ts` — added `tanstackStart.spa: { enabled: true }`.
  Without this the build produces **no static HTML at all**: this app is
  TanStack Start with SSR on by default, and `vite build` only emitted JS/CSS
  chunks plus a Cloudflare Worker server bundle, not an `index.html` — there
  was nothing for a Python container to serve as "static files." `spa:
  { enabled: true }` makes TanStack Start prerender a static SPA shell
  instead (confirmed with the user before making this frontend-side change,
  since the task as given only mentioned editing the Dockerfile).
- `backend/config.py` — added `FRONTEND_DIST_DIR` (default `frontend_dist`;
  absent/unused in local dev and in tests, since the directory doesn't
  exist there).
- `backend/main.py` — if `FRONTEND_DIST_DIR` exists, mounts `/assets` as
  `StaticFiles` and adds a catch-all `GET /{full_path:path}` route
  (registered after `api_router`) that serves the matching static file if
  one exists, else falls back to `index.html` for client-side routing;
  unmatched `/api/*` paths 404 instead of falling through to the frontend.

## Design notes / mismatches with the spec docs

- `_docs/specs.md` §28 documents backend env vars (`DATABASE_URL`,
  `ALLOWED_ORIGINS`) but not the new `FRONTEND_DIST_DIR` — not updated in
  this session (wasn't asked, and issue #5 isn't closed yet).
- Issue #5's scope line also names a Bun stage ("Stage 1 (Node/Bun)") and a
  Postgres driver / `docker-compose.yml` / Playwright E2E suite. This
  session only produced the Dockerfile + static-serving half; the user's
  literal request was "edit the Dockerfile ... build the frontend with
  Node," so the build stage uses plain `npm`/`node:22-slim` against
  `package.json`, not `bun`/`bun.lock` (which is what `Makefile` and CI use
  elsewhere in this repo).

## Verification

- `uv run pytest` — 52 passed, unchanged.
- `docker build -t restaurant-waitlist:test .` — succeeded.
- Ran the built image (`docker run -p 18091:8091 ...`) and confirmed:
  - `GET /` → 200, correct SPA shell HTML with real asset paths.
  - `GET /assets/index-*.js` → 200, `content-type: text/javascript`.
  - `GET /favicon.ico` → 200.
  - `GET /staff` (client-side route) → 200, SPA fallback serves `index.html`.
  - `GET /api/venue` → real venue JSON.
  - `POST /api/auth/login` (manager/waitlist123) → real token.
  - `GET /api/does-not-exist` → 404 (not swallowed by the SPA fallback).
- Removed the test image/container and local build artifacts
  (`frontend/.output`, `frontend/node_modules/.nitro`, `frontend/.wrangler`
  — all gitignored) afterward.

## Commands to validate

```
uv run pytest
docker build -t restaurant-waitlist:test .
docker run --rm -p 18091:8091 restaurant-waitlist:test
# then hit http://localhost:18091/, /staff, /api/venue, /api/auth/login
```

## Follow-ups for the next session

- Issue #5's remaining scope: `docker-compose.yml` (`app` + `postgres:16-alpine`
  with a healthcheck), a Postgres driver in `pyproject.toml`, wiring
  `DATABASE_URL=postgresql://...` via Compose, `tests/integration/` against
  the live stack, Playwright `e2e/` two-session (staff/guest) tests, and a
  `make e2e` target.
- Decide whether the frontend build stage should switch from `npm` to `bun`
  (matching `frontend/bun.lock` and the rest of the repo's tooling) once
  Compose/CI needs are clearer.
- Update `_docs/specs.md` §28 with `FRONTEND_DIST_DIR` once issue #5's
  Docker/Compose work is closed out.
