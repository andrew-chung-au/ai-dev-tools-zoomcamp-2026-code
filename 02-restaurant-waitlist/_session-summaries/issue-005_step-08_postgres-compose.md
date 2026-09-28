# Issue #5 — Step 8: Postgres driver + docker-compose.yml

Continues issue #5 ("Table Ready Deployment: Step 1 — Containerize and
migrate to Postgres via Docker Compose") after
[[issue-005_step-07_docker-static-frontend]]. Adds the Postgres driver and
the `docker-compose.yml` stack. Integration tests, Playwright E2E tests, and
`make e2e` from that issue are still **not** done — see Follow-ups.

## What changed

- `pyproject.toml` / `uv.lock` — added `psycopg2-binary>=2.9.13` via `uv add`
  (sync driver, matching `backend/db.py`'s plain `create_engine`/`sessionmaker`
  — no async SQLAlchemy in this codebase). No code changes needed in
  `backend/db.py`: it already only special-cases `sqlite://` URLs, so
  `postgresql://...` just works once the driver is installed.
- `docker-compose.yml` (was an empty placeholder file) — two services:
  - `postgres`: `postgres:16-alpine`, `waitlist`/`waitlist`/`waitlist`
    user/password/db, a named volume, and a `pg_isready` healthcheck.
  - `app`: builds from the repo's `Dockerfile`, publishes `8091`, sets
    `DATABASE_URL=postgresql://waitlist:waitlist@postgres:5432/waitlist`,
    and `depends_on: postgres: condition: service_healthy` so it doesn't
    start until Postgres is actually accepting connections.
- `Dockerfile` — changed the CMD from `uv run uvicorn ...` to `uv run
  --no-sync uvicorn ...`. Without `--no-sync`, `uv run` re-verifies the
  environment against `uv.lock` **on every container start**, including the
  `dev` dependency group (`pytest`, `httpx2`) that the image was built
  without (`uv sync --frozen --no-dev`) — this needs network access at
  container *runtime*, which failed outright inside `docker compose up`
  (DNS/connect errors to pypi) and is fragile/non-deterministic even when it
  succeeds. `--no-sync` uses the venv baked in at build time, as intended
  for a production image.

## Design notes / mismatches with the spec docs

- Postgres credentials (`waitlist`/`waitlist`) are plaintext in
  `docker-compose.yml`, fine for this local/course-project stack but not
  something to carry into a real deployment.
- `_docs/specs.md` §28 still only documents `DATABASE_URL`'s SQLite default
  and doesn't mention the Postgres path or `FRONTEND_DIST_DIR` (the latter
  was already flagged as a follow-up in step 07) — not updated here either.

## Verification

- **Sandbox networking limitation discovered and worked around for testing:**
  this session's Docker daemon silently drops all container-to-container TCP
  traffic on user-defined bridge networks (confirmed with a minimal
  alpine-to-alpine `nc` test on a fresh network — timeout, not refused;
  host networking and internet egress both work fine). This is an
  environment/sandbox restriction, not a problem with the compose file:
  `docker compose up` correctly builds, starts Postgres, waits for its
  healthcheck to go `healthy`, *then* starts `app` — but `app` then couldn't
  reach `postgres:5432` over the bridge in *this* sandbox.
  - Worked around by running the app image with `--network
    container:<postgres-container>` (shares Postgres's network namespace,
    bypassing the bridge) to prove the actual wiring:
    - `uv run --no-sync python -c "...SQLAlchemy engine.connect()..."` →
      `PostgreSQL 16.15 ...` (driver + `DATABASE_URL` work).
    - Ran the full app this way → `Application startup complete`, and
      `GET /api/venue` returned the real seeded venue JSON — schema
      creation and seeding both succeeded against real Postgres, not
      SQLite.
  - This workaround is not part of the shipped `docker-compose.yml`; on a
    normal (non-sandboxed) Docker host, `docker compose up --build` should
    work as configured, without it.
- `uv run pytest` — 52 passed, unchanged (tests still use per-test SQLite
  files via `tmp_path`, untouched by this change).
- Cleaned up all test containers, the ad-hoc `alpine`/`pingnet` connectivity
  probes, the compose stack (`docker compose down -v`), and the built test
  image afterward.

## Commands to validate

```
uv run pytest
docker compose up --build      # on a host without the sandbox's bridge restriction
# then hit http://localhost:8091/, /api/venue, /api/auth/login
docker compose down -v
```

## Follow-ups for the next session

- Issue #5's remaining scope: `tests/integration/` against the live Compose
  stack, Playwright `e2e/` two-session (staff/guest) tests, and a `make e2e`
  target.
- If this sandbox's bridge-network restriction also affects CI/other
  automated runs of `make e2e` later, the network-namespace-sharing
  workaround here won't generalize (compose manages its own containers) —
  that will need to run somewhere without this restriction, or the
  restriction will need addressing at the environment level.
- Update `_docs/specs.md` §28 with the Postgres `DATABASE_URL` shape and
  `FRONTEND_DIST_DIR` once issue #5's Docker/Compose work is closed out.
- Consider moving the Postgres credentials in `docker-compose.yml` to a
  `.env` file (gitignored) if this stack is ever used somewhere less
  disposable than local/course use.
