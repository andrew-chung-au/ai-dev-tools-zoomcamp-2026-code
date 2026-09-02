# Backlog

Small, sequential backlog for building the household chores app in Django,
derived from `docs/plan.md`. Each task is roughly one PR-sized unit of work.

## 1. Data model
Create `Person` and `Chore` models in the `chores` app.
- `Person`: name (unique within household).
- `Chore`: name, `assigned_to` (FK to Person), `last_done_at`, `done` flag or
  status.
- Rotation order needs a concrete field even before the algorithm is decided
  — e.g. a `Person.order` int or an ordered `rotation` list on `Chore` — so
  later tasks aren't blocked. **Depends on open question:** rotation
  order/algorithm among multiple people. Default to simple fixed list order
  (by `Person.order`) unless told otherwise.
- Leave chore metadata (frequency, difficulty/weight) out of v1 unless the
  open question gets resolved first — add fields only when there's a
  confirmed need.

## 2. Migrations + admin registration
Generate and apply migrations; register both models in `chores/admin.py` so
there's a working CRUD surface immediately, even before custom views exist.

## 3. Rotation logic
Implement "mark done" as a model method or service function:
- Marks the chore done, records `last_done_at`.
- Advances `assigned_to` to the next person in sequence.
- No time-based auto-rotation — this only runs on explicit mark-done.
- **Depends on open question:** how ties/skips are handled (person
  unavailable for their turn). Until decided, assume simple round-robin with
  no skip support.
- Unit tests for the rotation sequence (including wraparound past the last
  person).

## 4. Overdue detection
Add a way to compute "overdue" per chore (e.g. days since `last_done_at`
exceeds a threshold) and expose it as a boolean/property for templates to
key off of. Visual-only — no notification mechanism.

## 5. Dashboard view (shared-screen mode)
A single read-only-ish page listing all chores, who they're assigned to, and
an overdue highlight, plus a "mark done" control per chore. Built to work
unauthenticated on a shared/kiosk device — no login gating.

## 6. Same view on individual devices
Verify/adjust the dashboard's responsiveness so it works as-is from a phone
browser — this is the same view as #5, not a separate app, since there are
no accounts. Mostly a CSS/layout pass plus a manual check on a small
viewport.

## 7. People & chore management CRUD
Basic create/edit/delete forms for `Person` and `Chore`, reachable from the
dashboard, since management is ongoing rather than a one-time setup step.
Can start as thin views wrapping Django's generic CRUD views, or lean on
admin if that's judged sufficient for v1.

## 8. Seed/demo data
A management command or fixture to populate a sample household (a few
people, a few chores) for local testing and demoing the rotation.

## 9. Tests pass for full flow
End-to-end test: create people/chores, mark a chore done repeatedly, assert
assignment rotates correctly and overdue flag behaves as expected.

---

**Before starting #1**, resolve or explicitly punt on the three open
questions in `docs/plan.md` (chore fields, tie/skip handling, rotation
algorithm) — tasks above bake in a "simplest default" assumption for each so
work isn't blocked, but confirm with the user before those defaults harden
into shipped behavior.
