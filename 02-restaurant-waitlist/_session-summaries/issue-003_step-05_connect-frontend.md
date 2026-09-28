# Issue 003 — Step 05: Connect frontend to FastAPI backend

## What changed

Connected the existing frontend to the existing FastAPI backend (Step 4),
keeping the in-memory store — no database/SQLAlchemy/Alembic/Docker/CI
changes. The mock service and all route/UI code are untouched; only the
service layer was swapped.

- **Backend CORS**: `backend/main.py` now installs `CORSMiddleware` using an
  allowlist from a new `backend/config.py` variable, `ALLOWED_ORIGINS`
  (defaults to `http://localhost:8080` and `http://127.0.0.1:8080` — the
  frontend dev server's fixed port, pinned by
  `@lovable.dev/vite-tanstack-config`; overridable via an `ALLOWED_ORIGINS`
  env var). `allow_methods=["*"]` / `allow_headers=["*"]` so the browser can
  preflight `Authorization` and `Content-Type`.
- **Real HTTP service**: new `frontend/src/services/apiWaitlistService.ts`
  implements `WaitlistService` with `fetch`, one method per `openapi.yaml`
  operation. Base URL comes from `VITE_API_BASE_URL` (default
  `http://localhost:8091/api`, matching `backend/config.py`'s
  `DEFAULT_PORT`). Errors are wrapped in `ApiServiceError` (`{code,
  message}`), mirroring `MockServiceError`. The staff bearer token is
  captured in memory inside `login()` and attached as `Authorization: Bearer
  <token>` to every subsequent request — no separate auth system needed
  since routes never pass a token explicitly to the service.
- **Service switch**: `frontend/src/services/index.ts` now exports
  `ApiWaitlistService` by default (dev/build) and falls back to
  `MockWaitlistService` when `import.meta.env.MODE === "test"` (so Vitest is
  unaffected) or when `VITE_USE_MOCK_SERVICE=true` is set (for offline
  frontend work).

## Files created / modified

- `backend/config.py` — modified, added `ALLOWED_ORIGINS`.
- `backend/main.py` — modified, added `CORSMiddleware`.
- `frontend/src/services/apiWaitlistService.ts` — created.
- `frontend/src/services/index.ts` — modified, service-switch logic.
- `frontend/src/services/mockWaitlistService.ts` — unchanged (as required).

Not yet committed — this session stopped short of committing per the
orchestrating instructions for this task, so `git status --short` above still
shows these as working-tree changes. Follow-up: commit with a message such as
"Connect frontend to FastAPI backend (Step 5, issue #3)" per the issue's
acceptance criteria.

## Mismatches with specs/openapi/backend

None found. Every backend router path, parameter name, and request/response
schema (`backend/routers/*.py`, `backend/schemas.py`, `backend/models.py`)
matches `openapi.yaml` and the frontend `WaitlistService` interface exactly,
so `openapi.yaml` was left unchanged.

One behavioral divergence carried over from Step 4 (already noted in
`issue-002_step-04_fastapi-in-memory.md`, now visible from the frontend for
the first time): the mock accepts any non-empty login credentials, but the
real backend only accepts the seeded staff user (`manager` /
`waitlist123`). Not a bug — this is documented as intentional in the Step 4
summary and in the issue's own acceptance criteria — but worth remembering
when demoing: `login.tsx`'s copy ("Any non-empty username and password will
sign you in") is now only true when running against the mock.

## Commands to validate

```bash
# backend
cd 02-restaurant-waitlist
make run                       # uv run uvicorn backend.main:app --reload --port 8091
make test                      # uv run pytest — 52 passed

# frontend
cd 02-restaurant-waitlist/frontend
npm run dev                    # dev server on http://localhost:8080
                                # (bun is not installed in this environment; npm was used
                                # against the same package.json scripts — bun should work
                                # identically where available)
npm run test                   # vitest run — 30 passed
npm run build                  # production build — no TypeScript errors
```

## Manual end-to-end verification performed

Browser automation wasn't available in this session, so both servers were
started and every flow was driven with curl using the exact endpoints/headers
`ApiWaitlistService` sends (method, path, `Content-Type`, `Authorization`):

- CORS preflight (`OPTIONS`) and actual `GET /venue` from `Origin:
  http://localhost:8080` both return `access-control-allow-origin:
  http://localhost:8080` — no CORS errors.
- Guest join (`POST /waitlist-entries`, staff-review mode → `pending`) →
  guest status page (`GET /guest/entries/{token}`) → guest self-cancel
  (`POST /guest/entries/{token}/cancel`).
- Staff login: wrong credentials → `401`; `manager` / `waitlist123` → `200`
  with a session token. Unauthenticated `GET /dashboard` → `401`.
- Staff queue operations on the entry created by the guest-join call above
  (approve → notify → list-compatible-tables → seat at `tbl_1` → complete),
  plus a separate approve → cancel path — confirming data created by one
  "client" (the guest-join call, no token) is immediately visible to and
  operable by another "client" (the staff calls, bearer token) via the
  shared backend store, which is the cross-window behavior the issue asks to
  confirm.
- Table management: create, deactivate (`PATCH .../active`), delete (`204`).
- Large-party enquiries: both the direct `POST /large-party-enquiries`
  endpoint and the auto-redirect from an oversized `POST /waitlist-entries`
  guest join (`partySize` over `maxOnlinePartySize`) return a
  `LargePartyEnquiry` with a `kind: "large_party_enquiry"` result.
- Venue settings update (`PATCH /venue`) and notifications list (`GET
  /notifications`).

All responses matched the expected shapes/status codes from `openapi.yaml`.
Both dev servers were stopped at the end of the session.

## Follow-ups for next session

- Commit the four changed/new files above (see paths in "Files created /
  modified") with a message referencing issue #3, then push.
- Step 06: replace `InMemoryRepository` with SQLAlchemy/SQLite behind the
  same shape; `backend/services/*` and routers should not need to change,
  and neither should the frontend's `ApiWaitlistService`.
- Consider a `frontend/.env.example` documenting `VITE_API_BASE_URL` and
  `VITE_USE_MOCK_SERVICE` once the team has an opinion on whether `.env`
  files should be committed for this project (not added in this session to
  avoid unrequested config-file scope).
