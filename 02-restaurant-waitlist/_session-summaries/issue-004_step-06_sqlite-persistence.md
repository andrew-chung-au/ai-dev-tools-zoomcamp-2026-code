# Issue #4 — Step 6: SQLite persistence with SQLAlchemy

## What changed

Replaced the in-memory store with a SQLAlchemy-backed SQLite store, without
changing `backend/routers/*`, `backend/services/*`, or the frontend.

- `backend/db.py` (new) — `Base`, engine and session-factory helpers.
  SQLite-specific bits are limited to connection args (`check_same_thread`,
  `StaticPool` for `:memory:`), not SQL.
- `backend/orm_models.py` (new) — SQLAlchemy ORM classes (`VenueORM`,
  `StaffUserORM`, `TableORM`, `WaitlistEntryORM`, `LargePartyEnquiryORM`,
  `NotificationORM`, `CounterORM`), field-for-field matching the Pydantic
  models in `backend/models.py` (same camelCase names).
- `backend/repositories.py` (new) — `DatabaseRepository`, a drop-in
  replacement for `InMemoryRepository` exposing the same attributes/methods
  (`venue`, `tables`, `entries`, `enquiries`, `notifications`,
  `staff_users`, `sessions`, `find_entry`, `find_table`,
  `find_entry_by_access_token`, `next_id`, `next_ticket_sequence`,
  `next_access_token`). Collections return ORM rows attached to the
  request's session, so the in-place attribute mutations services already
  do (`entry.status = "seated"`, etc.) are tracked by SQLAlchemy and
  persisted on commit. `.append()` on a collection converts an incoming
  Pydantic instance to its ORM row and adds it to the session. `repo.tables
  = [...]` (used by `table_service.delete_table`) is handled by a
  setter that diffs against the current DB rows.
  Also carries `DatabaseRepository.seed()` / `seed_if_empty()`, ported
  directly from `InMemoryRepository._seed()`.
- `backend/config.py` — added `DATABASE_URL`, default
  `sqlite:///./waitlist.db`.
- `backend/main.py` — `create_app()` now takes an optional `database_url`
  override, builds an engine/session-factory, runs
  `Base.metadata.create_all()` and `seed_if_empty()` on startup, and stores
  the session factory + a shared staff-sessions dict on `app.state`.
- `backend/deps.py` — `get_repository` is now a per-request generator
  dependency: opens a `Session`, commits on success, rolls back on
  exception, always closes.
- `backend/models.py` — added `model_config = ConfigDict(from_attributes=True)`
  to `Venue`, `Table`, `WaitlistEntry`, `LargePartyEnquiry`, `Notification`
  so FastAPI's `response_model` can serialize ORM rows directly.
- `tests/conftest.py` — `client` fixture now points `DATABASE_URL` at a
  per-test temp SQLite file (via `tmp_path`) so tests stay isolated from
  each other and from a developer's local `waitlist.db`. Test logic
  unchanged.
- `.gitignore` — ignore `*.db` (the default SQLite file).
- `pyproject.toml` / `uv.lock` — added `sqlalchemy>=2.0` (confirmed with
  the user before adding, per `AGENTS.md`).

`backend/repository.py` (`InMemoryRepository`) was left in place but is no
longer wired up anywhere; nothing currently imports it.

## Design notes / mismatches with the spec docs

- The issue/spec text says "Create/update `backend/models.py` with
  SQLAlchemy ORM models". `backend/models.py` already holds the Pydantic
  domain/response models used directly as FastAPI response bodies
  throughout the app (`Table`, `Venue`, `WaitlistEntry`, ...), so adding
  same-named SQLAlchemy classes there would collide. ORM classes went into
  a new `backend/orm_models.py` instead; `backend/models.py` keeps its
  existing role, only gaining `from_attributes=True`.
- `StaffSession` (bearer tokens from login) is **not** persisted to the
  database — it lives in an `app.state.staff_sessions` dict shared across
  requests, matching the original in-memory behavior (sessions don't
  survive a restart either way, before or after this change).
- Importing `backend.main` builds the module-level `app = create_app()`
  using the default `DATABASE_URL`, which touches disk (creates
  `./waitlist.db` if missing) as a side effect of import — this already
  existed as a pattern before this change (module-level `app =
  create_app()`), just newly has an I/O side effect since the store isn't
  purely in-memory anymore. Not fixed here (would mean switching to
  `uvicorn ... --factory` or a lifespan handler, a bigger change than this
  issue calls for); mitigated by gitignoring `*.db`.

## Verification

- `uv run pytest` — 52 passed.
- Manual: started the backend against a temp `DATABASE_URL`, logged in as
  `manager`/`waitlist123`, created a guest entry, restarted the backend
  process, and confirmed the entry (and its id/ticket sequence) was still
  there. Also verified table create, approve/seat (entry status + table
  occupancy mutation), and a large-party enquiry all persist across a
  second restart.
- `make run` still starts the app on port 8091 (uses
  `backend.main:app`, unchanged entrypoint).

## Commands to validate

```
uv sync
uv run pytest
make run   # then hit http://localhost:8091/api/venue
```

## Follow-ups for the next session

- Two files (`_docs/specs.md`, `frontend/README.md`) already had
  `DATABASE_URL`/env-var documentation added by another session before
  this one started (visible in `git diff` at the start of this session) —
  left as-is, content is accurate and covers deliverable #7's docs
  requirement.
- `backend/repository.py` (`InMemoryRepository`) is now dead code; left
  in place rather than deleted, since removing it wasn't asked for.
