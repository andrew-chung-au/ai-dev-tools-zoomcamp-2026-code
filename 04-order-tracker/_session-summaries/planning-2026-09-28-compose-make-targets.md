# Planning: codebase review and Compose make targets

**Date:** 2026-09-28
**Spec version:** none

## What changed and why

Reviewed the README and codebase (FastAPI + SQLite app, static page, single `app` Compose service) and checked `AGENTS.md` and the `Makefile` against them. Starting the stack was already covered by `make run` (`docker compose up --build -d --wait`), so no duplicate target was added. Added `make stop` (`docker compose down`, keeps the `orders` volume) and `make logs` (`docker compose logs -f app`), the matching Commands slots in `AGENTS.md`, and the **Commits** project setting. Changes approved by the human in this session; left uncommitted at their request.

## Files created or modified

- `Makefile`: added `stop` and `logs` targets.
- `AGENTS.md` (protected): Run slot detail, new Stop and Logs slots, new **Commits** setting.
- `_session-summaries/planning-2026-09-28-compose-make-targets.md`: this file.

## Mismatches with the spec or design docs

No spec yet (`_docs/specs.md` doesn't exist). `AGENTS.md` and the Makefile match the README and code.

## Commands to validate

- **Run:** `make run`, then **Logs:** `make logs`, then **Stop:** `make stop` (all three smoke-tested this session)
- **Test (all):** `make test` (3 passed)
- **Verify:** `make verify`

## Proposed AGENTS.md changes

- Confirm or correct the **Branching** line ("commit directly to `main`", currently marked as observed, not confirmed).

## Unrelated problems noticed but not fixed

- `app/main.py` `order_detail`: `placed_at.replace(day=placed_at.day + 2)` raises `ValueError` (HTTP 500) for express orders placed in the last two days of a month. The seeded `express-1002` is always dated on the last day of the previous month, so `GET /api/orders/express-1002` should always fail. No test covers an express lookup. Probably the exercise's intended incident; left untouched.

## Follow-ups for the next session

- Commit `Makefile`, `AGENTS.md` (with `HUMAN_APPROVED=1`) and this summary once the human is ready.
- Homework 4: add telemetry, alerts and the incident responder (likely new Compose services; then consider `make logs` for all services).
