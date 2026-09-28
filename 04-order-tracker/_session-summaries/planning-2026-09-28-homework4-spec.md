# Planning: Homework 4 spec

**Date:** 2026-09-28
**Spec version:** none (`_docs/specs.md` written, not yet committed)

## What changed and why

Drafted `_docs/specs.md` from the Homework 4 text (Q2–Q6), the README, the code and the part 4 lesson ("DevOps and Observability for an AI-Built App"). The spec covers the questions one by one, the fixed interfaces the homework's test commands depend on (order lookup route, seed ids, responder at `POST /alerts` on port 8001, the ResponderTest payload, the one-command rebuild) and what's out of scope. The human approved the text in this session and asked for it to be written but not committed.

Where the lesson and the homework differ, the human approved these recommendations:
- **R1:** observability config lives in `observability/`, but its services join the main `compose.yaml` (for example with `include:`), so `docker compose up --build -d --wait` starts everything.
- **R2:** the responder receives webhooks in `incident-response/` (homework), instead of polling from `on-call-engineer/` (lesson). It reuses the lesson's on-call prompt.
- **R3:** low alert threshold (any 5xx in 5 min) with a pending period of about 1 minute.
- **R4:** the responder runs as a host process using `claude -p`. Grafana reaches it at `host.docker.internal:8001`.
- **R5:** no bug is introduced; the seeded `express-1002` bug is the incident.
- **R6:** all ports are bound to `127.0.0.1`.

## Files created or modified

- `_docs/specs.md` (protected, new): the Homework 4 spec.
- `_session-summaries/planning-2026-09-28-homework4-spec.md`: this file.

## Mismatches with the spec or design docs

- The spec needs a different rebuild behavior (fixed interface 5): `make run` / `docker compose up --build -d --wait` must also start the observability stack. The Compose file currently has only `app`. The spec calls for this, so it's expected work rather than a defect.
- The README's API table matches the spec's baseline.

## Expected homework answers (derived from the code, to confirm when each step is built)

- **Q2:** `200`. `standard-1001` is seeded.
- **Q3:** `404`. `standard-1002` isn't seeded.
- **Q4:** `Normal`. A 404 isn't a 5xx, and no-data is handled as Normal.
- **Q5:** depends on the agent's output. Expected: it reports a test notification with nothing to fix. Record the last line when it runs.
- **Q6:** "The express delivery date calculation tried to use a day that does not exist in that month." `order_detail` does `placed_at.replace(day=placed_at.day + 2)`, and `express-1002` is dated on the last day of the previous month, so the lookup raises `ValueError` → 500.

## Commands to validate

- **Test (all):** `make test`
- **Verify:** `make verify`
- Nothing to run for the spec itself. It's a document.

## Proposed AGENTS.md changes

- Once Q3 lands: Run/Stop/Logs should describe the full stack, and `make logs` may need to cover all services.
- Once Q5 lands: add a command slot for starting the responder (for example `make responder`).
- Still open from the earlier planning session: confirm the **Branching** line.

## Unrelated problems noticed but not fixed

- none new (the express date bug is the intended Q6 incident and is recorded in the spec).

## Follow-ups for the next session

- Commit the spec on its own (protected file, human already approved the text): see the suggested commit message below.
- Commit the pending changes from the earlier planning session (`Makefile`, `AGENTS.md`, `planning-2026-09-28-compose-make-targets.md`), which are still staged.
- With the spec in place, the PM builds the backlog (suggested split: one issue per question, Q2–Q6).

## Suggested commit message

For the spec (commit on its own, with `HUMAN_APPROVED=1 git commit ...`, after `git add _docs/specs.md`):

```
Add Homework 4 spec: observability, 5xx alert and on-call responder

Define the order-tracker spec for Homework 4 (Q2-Q6): OpenTelemetry
instrumentation, Collector/Prometheus/Loki/Tempo/Grafana pipeline,
a 5xx alert, and a webhook-driven responder on port 8001 that starts a
headless coding agent. Pin the interfaces the homework's test commands
depend on and list what's out of scope. Aligns with the part 4 lesson,
with approved deviations (single compose entry point, webhook instead
of polling, host-run responder).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

For this summary (separate commit, after `git add _session-summaries/planning-2026-09-28-homework4-spec.md`):

```
Add session summary for Homework 4 spec planning

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
