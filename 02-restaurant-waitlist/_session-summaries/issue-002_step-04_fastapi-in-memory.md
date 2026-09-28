# Issue 002 — Step 04: FastAPI backend with in-memory store

## What changed

Implemented the FastAPI backend in `backend/` against `openapi.yaml`, backed
entirely by an in-memory repository (no database). All 25 operations across
8 tags (auth, venue, dashboard, waitlist-entries, guest, tables,
large-party-enquiries, notifications) are implemented and verified to match
the OpenAPI paths/methods and `security: []` annotations exactly (checked
programmatically by diffing `app.openapi()` against the parsed spec).

Structure:

- `backend/models.py` — persisted entity models (Venue, Table, WaitlistEntry,
  LargePartyEnquiry, Notification, StaffSession, StaffUser), camelCase fields
  to match the contract.
- `backend/schemas.py` — request bodies and derived/composite response shapes
  (GuestStatus, DashboardData, CreateGuestEntryResult variants, etc).
- `backend/repository.py` — `InMemoryRepository`, seeded with one venue, one
  staff user (`manager` / `waitlist123`), 6 tables (varied capacities,
  `available` / `needs_tidying` / inactive states), and 7 waitlist entries in
  different statuses (pending, waiting, notified incl. one overdue, seated,
  and one with a party-size change producing `reviewRequired`).
- `backend/services/*` — business logic per area (auth, venue, tables,
  waitlist, large-party, notifications), translated 1:1 from
  `frontend/src/services/mockWaitlistService.ts` so behavior matches the
  frontend mock (ticket numbering/classes, sort order, needs-attention,
  seating constraints, table availability transitions, etc).
- `backend/security.py` / `backend/deps.py` — bearer-token sessions issued by
  `POST /auth/login`, checked via a `require_staff` FastAPI dependency applied
  to every non-guest route; guest/public routes have no such dependency,
  matching `security: []` in the contract.
- `backend/notifications.py` — `NotificationProvider` abstraction with a
  `ConsoleNotificationProvider` (prints to stdout) so a real provider can be
  swapped in later without touching services.
- `backend/errors.py` / exception handler in `main.py` — `ServiceError(status,
  code, message)` maps to the `Error` schema `{code, message}`.

One intentional divergence from the frontend mock: `POST /auth/login`
actually validates username/password against the seeded staff user (the mock
accepts any non-empty credentials) — required by this issue's acceptance
criteria ("succeeds with valid credentials and fails with invalid ones").

## Files created

- `pyproject.toml`, `uv.lock`, `Makefile` (repo root of `02-restaurant-waitlist/`)
- `backend/` (see structure above) — `backend/.gitkeep` removed (dir no longer empty)
- `tests/` — `conftest.py` + 6 test modules — `tests/.gitkeep` removed

## Mismatches with specs/docs

- `_docs/testing-guidelines.md` and `_docs/design-system.md`, referenced by
  `AGENTS.md`, do not exist in the repo. Not needed for this backend-only
  task; flagged here in case a future session expects them.
- `_docs/specs.md` §6 describes a setup wizard (no seeded default password)
  and password hashing for the first admin account. This issue's acceptance
  criteria explicitly asks for a seeded known staff user instead ("at least
  one staff user with known username/password for local testing"), so the
  setup wizard is out of scope here and left for a future step. Passwords are
  still hashed (SHA-256) rather than stored in plaintext.
- Venue `waitlistOpen` is a plain overridable boolean; the weekly schedule
  (spec §10) is not implemented — matches the frontend mock's scope for
  Module 2.

## Commands to validate

```bash
cd 02-restaurant-waitlist
uv sync
make test   # 52 passed
make run    # serves on http://localhost:8091, /docs for Swagger UI
```

Manual smoke test performed: login, protected-endpoint 401s, guest join
(staff-review → pending, automatic → waiting), large-party enquiry via
oversized party, approve → seat → complete flow (table goes
available → occupied → needs_tidying), table CRUD and availability
transitions.

## Follow-ups for next session

- Step 05: connect the frontend to this backend (replace `MockWaitlistService`
  with an HTTP client implementing the same `WaitlistService` interface).
  Will likely need CORS middleware added to `backend/main.py` at that point.
- Step 06: replace `InMemoryRepository` with SQLAlchemy/SQLite behind the same
  shape; services and routers should not need to change.
