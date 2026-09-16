# Session 2 — `test_flow.py` integration test for acceptance scenario 1

Continues [[session-01_architecture-review-and-local-run]]. The server
started in that session was still running in the background
(`uv run uvicorn main:app --reload` at `http://127.0.0.1:8000/`, confirmed
via `GET /health` → `200` before writing the test).

## What changed

### `test_flow.py` (new)

An httpx-based integration test that exercises SPEC.md's first acceptance
scenario end to end, against the live running server (not an in-process
`TestClient`):

1. Register two agents (`flow-sender`, `flow-recipient`) via
   `POST /api/v1/agents`, keeping each one's secret token.
2. Sender sends a task to the recipient via `POST /api/v1/tasks`; asserts
   `201` and `status == "queued"`.
3. Recipient claims it via `POST /api/v1/tasks/claim` (`wait_seconds: 5`);
   asserts the returned `task_id` matches and captures the `claim_token`.
4. Recipient completes it via `POST /api/v1/tasks/{task_id}/complete` with
   that claim token and an output string.
5. Sender reads the task back via `GET /api/v1/tasks/{task_id}` using its
   own bearer token and asserts `status == "completed"` with the expected
   output.

Each step asserts on status codes and response bodies, and the final status
is printed explicitly (`uv run pytest test_flow.py -v -s`) rather than only
asserted, per the task's request to "print the resulting task status."

## Result

```
Final task status (sender's view): completed
Output: No issues found.
PASSED
```

1 passed in 0.20s. The sender sees `completed` (not `queued`, `processing`,
or `delivered` — `delivered` isn't a status this API uses at all; see the
lifecycle diagram in `SPEC.md`: `queued -> processing -> completed`).

## Notes for next session

- `test_flow.py` requires the server to already be running — it is a
  live-integration test, not a fixture-managed one like
  `test_agent_relay.py` (which likely uses `TestClient`/in-process app).
  If this file is meant to be part of the regular suite going forward, it
  may need a `pytest` marker (see the `integration` marker convention used
  in the `02-restaurant-waitlist` module's `tests/integration/`) so
  `uv run pytest` alone doesn't fail when no server is up.
- The background Uvicorn process from session 1 is still running on
  `:8000`; check it's alive (or restart it) before rerunning this test in a
  future session.
