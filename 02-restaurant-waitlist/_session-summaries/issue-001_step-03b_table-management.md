# Step 3b summary — Basic staff table management

Issue: #1 — Module 2: Step 3b — Extend frontend service, mock, and OpenAPI for
basic table management.

## What changed

Extended the frontend service layer, mock implementation, Tables tab UI, and
`openapi.yaml` so staff can create, edit, activate/deactivate, delete, and
change the availability of tables. No backend, database, or deployment code
was added. Nothing was staged or committed.

### Service layer (`frontend/src/services/waitlistService.ts`)

- `Table` reshaped to match `_docs/specs.md` §9: `capacity`/`occupied`
  replaced with `minCapacity`, `maxCapacity`, `active`, `availabilityState`
  (`"available" | "occupied" | "needs_tidying"`), `notes` (nullable).
  `occupyingTicketCode`/`occupyingEntryId` kept for UI display.
- Added `CreateTableRequest`, `UpdateTableRequest`, `SetTableAvailabilityRequest`.
- Added `createTable`, `updateTable`, `deleteTable`, `setTableAvailability` to
  the `WaitlistService` interface.

### Mock implementation (`frontend/src/services/mockWaitlistService.ts`)

- Seeded 6 demo tables with varied capacity ranges (1-2, 2-4, 4-6): one
  inactive table, one `needs_tidying` table, the rest `available`/`occupied`.
- `seatEntry` validates `active`, `availabilityState === "available"`, and
  both capacity bounds, with distinct error codes: `table_inactive`,
  `table_occupied`, `table_not_available`, `table_too_small`,
  `table_capacity_mismatch`.
- `completeEntry` now releases a table to `needs_tidying` (not straight to
  `available`), per spec.
- New `createTable` / `updateTable` / `deleteTable` / `setTableAvailability`.
  `setTableAvailability` enforces the spec's manual-transition rules:
  `needs_tidying → available` only from `needs_tidying`; `→ needs_tidying`
  allowed from `available` or `occupied` (clearing the occupying entry in the
  latter case, per §9's "guests leave without being properly checked out"
  case). Deleting an occupied table is rejected.

### UI (`frontend/src/routes/staff.tables.tsx` — full rewrite;
`frontend/src/routes/staff.index.tsx` — 1-line fix for the renamed capacity
field in `SeatDialog`)

- List/create/edit/activate/deactivate/delete tables, plus manual "Mark
  available"/"Mark needs tidying" actions, using the existing design-system
  patterns (`surface-card`, `Overlay`, `ActionButton`) already used by
  `staff.index.tsx` / `staff.settings.tsx`. (`_docs/design-system.md` and
  `_docs/testing-guidelines.md`, referenced by `AGENTS.md`, do not exist in
  this repo, so no additional guidance could be checked there.)

### Tests (`frontend/src/services/__tests__/mockWaitlistService.test.ts`)

- Updated existing seating/completion tests for the new field names and the
  `needs_tidying`-after-completion behavior.
- Added coverage for inactive/needs_tidying seating rejection and the new
  table-management methods (create, update, delete, availability
  transitions, occupied-table protections).

### `openapi.yaml`

- Added `POST /tables`, `PATCH /tables/{tableId}`, `DELETE /tables/{tableId}`,
  `PATCH /tables/{tableId}/availability`.
- Extended `Table` schema with `minCapacity`, `maxCapacity`, `active`,
  `availabilityState`, `notes`.
- Added `TableAvailabilityState`, `CreateTableRequest`, `UpdateTableRequest`,
  `SetTableAvailabilityRequest` schemas.
- Documented the available-only seating constraint on the `Table` schema, the
  `seatEntry` operation, and `setTableAvailability`.

## Files created or modified

```
frontend/src/routes/staff.index.tsx
frontend/src/routes/staff.tables.tsx
frontend/src/services/__tests__/mockWaitlistService.test.ts
frontend/src/services/mockWaitlistService.ts
frontend/src/services/waitlistService.ts
openapi.yaml
_session-summaries/issue-001_step-03b_table-management.md   (this file, new)
```

`AGENTS.md`, `_docs/process.md`, and `_docs/specs.md` show as modified in
`git status` but those changes predate this session and were not made as
part of this work.

## Mismatches / assumptions vs. `_docs/specs.md` §9

1. Seating enforces **both** `minCapacity` and `maxCapacity` as hard
   constraints (a party of 2 cannot be seated at a 4-6 table). The spec only
   explicitly says seating fails when "capacity is insufficient" (a ceiling),
   not that a floor is enforced — this is an interpretation added to make
   `minCapacity` meaningful for seating, not just descriptive. Worth
   confirming; easy to relax if oversized-table seating should be allowed.
2. Manually marking an **occupied** table `needs_tidying` is implemented per
   the §9 transitions text ("Staff can also manually mark an `occupied`
   table as `needs_tidying`"), even though the separate "Table management
   UI" bullet list only mentions toggling between `available` and
   `needs_tidying`. Documented in the OpenAPI `setTableAvailability`
   description.
3. Deleting an occupied table is blocked — not explicitly required by the
   spec, but added as a safety guard consistent with "cannot be seated at an
   occupied table."

## Commands to validate

```bash
# OpenAPI
python3 -m openapi_spec_validator openapi.yaml   # -> "openapi.yaml: OK"

# Frontend (no `bun` binary was available in this environment; used npm
# as a substitute against the existing package.json scripts)
cd frontend
npm install
npx tsc --noEmit -p .    # clean
npm test                 # 30/30 passed
npm run build            # client + SSR + nitro build succeeded
```

`git diff --check` is clean (no whitespace errors). `frontend/package-lock.json`,
generated as a side effect of substituting `npm` for `bun`, was deleted again
after testing so it doesn't pollute the bun-based repo.

## Follow-up notes for the next session

- `bun` is not installed on this machine; future sessions in this
  environment will need the same npm substitution, or `bun` should be
  installed first if strict parity with `bun.lock` is required.
- `_docs/design-system.md` and `_docs/testing-guidelines.md` are referenced
  by `AGENTS.md` but do not exist in the repo — either create them or update
  `AGENTS.md` to stop pointing at them.
- Confirm the two capacity/transition interpretations above (min-capacity
  floor on seating; manual occupied → needs_tidying) match intent before the
  backend (Step 4) encodes them as hard business rules.
