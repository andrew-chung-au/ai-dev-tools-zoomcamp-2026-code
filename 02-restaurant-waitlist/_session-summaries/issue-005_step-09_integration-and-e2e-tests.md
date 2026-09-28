# Issue #5 — Step 9: Postgres integration tests + Playwright e2e suite

Continues issue #5 ("Table Ready Deployment: Step 1 — Containerize and
migrate to Postgres via Docker Compose") after
[[issue-005_step-08_postgres-compose]], closing out that step's listed
follow-ups: `tests/integration/` against the live Compose stack, a
Playwright `e2e/` two-session (staff/guest) suite, and a `make e2e` target.

## What changed

### `tests/integration/` (pytest, against the live docker-compose stack)

- `tests/integration/conftest.py` — a session-scoped `docker_stack` fixture
  that reuses an already-running stack if one answers on `:8091`, otherwise
  runs `docker compose up -d --build` itself and tears it back down only if
  it was the one that started it (so it never kills a stack a developer is
  using for something else). A `postgres_query` fixture runs SQL directly
  against Postgres via `docker compose exec app uv run --no-sync python
  -c "..."`, using the `app` container's own `DATABASE_URL` and its
  already-installed `psycopg2` — independent of the API, so it actually
  proves persistence in Postgres rather than trusting the API's own
  response.
- `tests/integration/test_postgres_connectivity.py` —
  `test_guest_entry_round_trips_through_postgres`: posts a guest join to the
  live backend, reads it back via `GET /api/guest/entries/{accessToken}`,
  then independently confirms the row in the real `waitlist_entries` table
  with a direct query.
- `pyproject.toml` — registered an `integration` pytest marker and added
  `addopts = "-m 'not integration'"` so the documented `uv run pytest`
  ("the whole suite") stays fast and Docker-free; the new test runs
  explicitly via `uv run pytest tests/integration -m integration`.

### `e2e/` (Playwright, against the live docker-compose stack)

- `e2e/package.json` — a standalone npm project (`@playwright/test`
  devDependency only). Uses **npm**, not `bun`, deliberately: `bun` isn't
  installed in this session's sandbox at all, and Playwright's own tooling
  (`playwright install`, `playwright install-deps`) is validated against
  Node: npm is the safer, more portable choice for this new suite even
  though `frontend/` uses `bun` for its own tests.
- `e2e/playwright.config.ts` — `baseURL` defaults to
  `http://localhost:8091` (the `app` service's published port, serving both
  API and built frontend from one origin, same as `docker-compose.yml`),
  overridable via `E2E_BASE_URL`. No `webServer` block — the compose stack
  is brought up by `make e2e`, not by Playwright itself.
- `e2e/tests/staff-sees-guest-realtime.spec.ts` — the two-session flow:
  1. Session 1 (its own `BrowserContext`): sign in at `/login` as
     `manager`/`waitlist123` (the seeded staff user — see
     `backend/repositories.py`), land on `/staff`, and read the "Pending
     review" summary count.
  2. Session 2 (a second, fully independent `BrowserContext` — separate
     cookies/localStorage): open `/join` and submit a guest entry.
  3. Back on session 1, **without reloading or clicking anything**, wait
     (up to 25s) for the "Pending review" count to increment by one on its
     own, then use the dashboard's own "Refresh" button and assert the new
     guest's row (name + ticket code) appears.
- `e2e/.gitignore` — `node_modules/`, `test-results/`, `playwright-report/`,
  etc.
- `Makefile` — new `e2e` target: `docker compose up -d --build`, a curl
  loop waiting for `http://localhost:8091/api/venue` to respond (the `app`
  service has no healthcheck of its own, unlike `postgres`), then
  `(cd e2e && npm install && npx playwright install --with-deps chromium
  && npm test)`, then `docker compose down` regardless of the test outcome
  (propagating the test exit code).

## Design notes: what "real-time" actually means in this app

The frontend has **no websocket/SSE channel** — everything is HTTP polling
(confirmed by grep: no `websocket`/`sse`/`EventSource` anywhere in
`backend/` or `frontend/src/`). Specifically, in
`frontend/src/routes/staff.index.tsx`:

- `dashboardQuery` (the summary cards — Active waiting / Pending review /
  Notified / Needs attention) has `refetchInterval: 20_000` — this really
  does auto-update with zero user interaction.
- `entriesQuery` (the actual list of guest rows) has **no**
  `refetchInterval` at all — it only refetches when the "Refresh" button is
  clicked or after a staff action (approve/notify/etc).

So "the staff dashboard sees the new guest appear in real-time" is tested
as: the summary count increments on its own (genuine, unattended, polling
"real-time"), and then the row itself is confirmed via the same "Refresh"
click a real staff member would use — not a page reload. This is called out
in a comment at the top of the spec so it doesn't read as a flaky wait for
something that isn't actually implemented as push-based.

## Verification

- `uv run pytest` — 52 passed, 1 deselected (the new integration test),
  unchanged from before this session.
- **`tests/integration`**: ran `uv run pytest tests/integration -m
  integration` for real. `docker compose up -d --build` built and started
  both containers, but `app` timed out connecting to `postgres` — this is
  the same sandbox bridge-network restriction already documented in
  [[issue-005_step-08_postgres-compose]] (confirmed again here with a
  plain `alpine` container: `nc`/`ping` to another container on the same
  compose network both time out). Not a regression or a bug in the test;
  tore the stack down afterward (`docker compose down`).
- **`e2e/`**: since the same restriction blocks the compose stack itself in
  this sandbox, validated the Playwright spec against an equivalent,
  non-compose stand-in that exercises the identical code paths: built the
  real frontend (`cd frontend && npm run build`, moving `_shell.html` to
  `index.html`, exactly like the `Dockerfile`'s frontend-build stage) and
  ran the real backend directly (`uv run uvicorn backend.main:app --port
  8091`) with `FRONTEND_DIST_DIR` pointed at that build — i.e. the same
  single-origin `:8091` setup `docker-compose.yml` produces, just with
  SQLite instead of Postgres (a difference `backend/db.py` treats as a
  config-only URL swap, and which step 08 already proved works
  end-to-end against real Postgres via a network-namespace workaround).
  Installed Playwright (`npx playwright install chromium` +
  `sudo npx playwright install-deps chromium` — needed system libs like
  `libatk-1.0.so.0` that a bare npm install doesn't pull in) and ran
  `npm test`: **1 passed in ~23s**, confirming the login, cross-context
  guest join, the unattended 20s summary-count poll, and the
  Refresh-then-see-the-row step all work exactly as written. Cleaned up
  the backend process, the frontend build output, and all compose
  containers afterward.
- `make e2e` itself (the full compose-orchestrated path) was not exercised
  end-to-end here for the same reason `tests/integration` couldn't be — the
  sandbox's container-to-container networking restriction, not anything in
  the Makefile/Playwright config.

## Follow-ups for the next session

- Run `make e2e` and `uv run pytest tests/integration -m integration` on a
  normal (non-sandboxed) Docker host — both should just work as configured;
  nothing here is expected to need changes there.
- Repeated `make e2e` runs accumulate demo waitlist entries in the
  `postgres-data` volume (the test asserts a *delta* in the pending count,
  so it's robust to this, but it's not tidy). Consider `docker compose down
  -v` at the end of the `e2e` Makefile target if a clean slate per run is
  preferred over speed/inspectability of leftover state.
- If a real push-based update (websocket/SSE) is ever added for the staff
  entries list, revisit `staff-sees-guest-realtime.spec.ts` — the
  "click Refresh" step exists only because that list currently has no
  polling of its own.
