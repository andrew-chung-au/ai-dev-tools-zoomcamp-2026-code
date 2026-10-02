# Issue #011 follow-up: full Q6 run

**Date:** 2026-10-02
**Spec version:** `8ee8884`

## What changed and why

The human ran the full Q6 check that #11 left as a follow-up: a real 5xx alert from Grafana, delivered to the responder with dry run off, so the on-call agent investigates and fixes it. Sources: `.scratch/responder.log` (deleted afterwards by `make clean-scratch`) and `incident-response/incidents/20261002T052640Z-Order_Tracker_5xx_responses/` (git-ignored).

- **Responder:** listened on `172.17.0.1:8001`, dry run off, from 05:24:30Z.
- **Deliveries** (all from Grafana at `10.215.24.7`):
  - one `401 Unauthorized`; the log doesn't say why;
  - one resolved notification, accepted (`202`) and skipped;
  - **05:26:40Z:** the firing `Order Tracker 5xx responses` alert for `/api/orders/{order_id}` (starts 05:26:10Z, about 4.11 5xx in 5 minutes), accepted (`202`).
- **Evidence collected:** Loki returned 4 log lines, all lookups of `express-1002`; Tempo returned 3 traces with 500 on `GET /api/orders/{order_id}`. Both queries returned 200.
- **Agent:** started 05:26:40Z, finished 05:28:06Z with exit code 0 and `RESULT: FIXED`. It committed `42b42f1` (not pushed):
  - `app/main.py`: the express delivery estimate used `placed_at.replace(day=placed_at.day + 2)`, now `placed_at + timedelta(days=2)`;
  - `tests/test_api.py`: regression test `test_express_order_placed_at_month_end`;
  - `tests/test_telemetry.py`: two server-error tests relied on this bug to get a 500; they now use a `failing_lookup` fixture that raises on purpose, with their assertions unchanged. The agent flagged this for review;
  - its `make verify`: PASS, 167 tests, no weakened tests.
- **Live check (agent):** `make probe URL=http://localhost:8000/api/orders/express-1002` returns `200 OK` (created 2026-08-31, estimated delivery 2026-09-02). The human confirmed the request now returns 200.

**Q6 answer:** the express delivery date calculation tried to use a day that doesn't exist in that month. Adding 2 to the day number of an order placed in the last two days of a month (such as the seeded `express-1002`, placed on the last day of the previous month) asks for a day like August 32, so Python raises `ValueError: day is out of range for month` and the endpoint returns 500.

## Files created or modified

- By the agent during the run: `app/main.py`, `tests/test_api.py`, `tests/test_telemetry.py` (`42b42f1`)
- Git-ignored: `incident-response/incidents/20261002T052640Z-Order_Tracker_5xx_responses/` (payload, logs, traces, summary, agent output and status)
- This summary

## Decisions made by the human

- Ran the full Q6 check with dry run off.
- Removed the #11 firewall rule after the run (below).
- Approved `make clean-scratch` after this summary is committed.

## Mismatches with the spec or design docs

None found.

## Commands to validate

- **Verify:** `make verify`
- **Run:** `make run`, then **Probe:** `make probe URL=http://localhost:8000/api/orders/express-1002` (expect `200`)

## Proposed AGENTS.md changes

None.

## Temporary changes

- **Firewall rule from #11** (`DOCKER-USER`, `10.215.24.0/24` to `10.215.24.0/24`): removed. On 2026-10-02 the human's `-D` reported no matching rule, and `sudo iptables-legacy -S DOCKER-USER` shows only the default `-A DOCKER-USER -j RETURN`. To add it back for a later run, see "Known environment issues" in the README.
- **Responder:** stopped; its log ends with "Finished server process".
- **Large installs:** `.scratch/node_modules/`, deleted by `make clean-scratch` along with the rest of `.scratch/`.

## Interruptions

None.

## Unrelated problems noticed but not fixed

- The run's first delivery got `401`. Possibly a token mismatch between Grafana and the responder at that moment, but that's unconfirmed. Later deliveries got `202`.
- `42b42f1` ends with a `Co-Authored-By` line; under agent kit 1.7 (`c65378d`), attribution comes from the tool's settings instead.

## Follow-ups for the next session

- Review `42b42f1`, in particular the `tests/test_telemetry.py` fixture change, then push.
- #14, #15, #16 and #12 are unchanged.

## Suggested commit message

```
Add session summary for the full Q6 run

Record the alert delivery at 05:26:40Z, the on-call agent's fix in
42b42f1 (express delivery date overflowing the month), the Q6 answer,
and that the #11 DOCKER-USER firewall rule is removed.

Generated with Claude Code
```
