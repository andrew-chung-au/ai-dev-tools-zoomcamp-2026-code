# Issue #007: Order Tracker: Q2 — Instrument order lookups with OpenTelemetry (console export)

**Date:** 2026-09-28
**Spec version:** 5161b1d

## What changed and why

Worked #7 following `_docs/agent-kit/process.md`, with PM, Engineer and QA run as subagents.

- **Start of session:** the only spec commit since the last recorded version (`baa3f14`) was `5161b1d`, the responder bind/token exception (Q5/Q6). It came out of the backlog grooming and was already folded into #10 and #11. It doesn't touch Q2, so no separate backlog review was run.
- **PM:** made four edits to #7. It added a criterion that the 404 span must not be ERROR, required at least one structured log record per lookup with the trace and span IDs, made the "instrumented once" criterion checkable with a test, and asked for the env var names in the issue comment. The human then decided on custom env vars `DEPLOYMENT_ENVIRONMENT` (default `local`) and `SERVICE_VERSION` (default `ORDER_TRACKER_TAG`, then `local`), with the resource key `deployment.environment`. The PM added both to #7's Constraints.
- **Engineer:** added `app/telemetry.py`, with console exporters for traces, metrics and logs, FastAPI auto-instrumentation, a 5 s metric export interval and `/healthz` excluded. It uses the stable HTTP conventions, so the route is in `http.route`. `get_order` now logs `order lookup` (plus `order not found` on a 404). `compose.yaml` sets both env vars. `tests/conftest.py` installs in-memory providers, and 16 new tests are in `tests/test_telemetry.py`. `order_detail` and API behavior are unchanged.
- **QA:** PASS on all 19 criteria, checked live with `make run`, curl and `make logs` as well as `make verify`. Assert clean passed and HEAD was unchanged (`f48ecd9`).
- **AGENTS.md:** the human approved the Engineer's layout and telemetry-gotcha update, committed on its own.

### Q2 findings (where to look in `make logs`)

- **Request metric:** `"name": "http.server.request.duration"`, with data points `"http.route": "/api/orders/{order_id}"`, `"http.request.method": "GET"` and `"http.response.status_code": 200` (or 404 / 500). A 500 also has `"error.type": "500"`. It is exported every 5 s, and because it's cumulative it is printed again every interval.
- **Span:** `"name": "GET /api/orders/{order_id}"`. The `express-1002` span has `"status_code": "ERROR"` and an `exception` event with `"exception.type": "ValueError"`.
- **Logs:** `"body": "order lookup"` / `"order not found"`, with `trace_id` and `span_id` matching the request span.
- **Resource on every signal:** `service.name=order-tracker`, `deployment.environment=local`, `service.version=local` (the defaults).

## Files created or modified

- `app/telemetry.py` (new)
- `app/main.py`
- `compose.yaml`
- `pyproject.toml`, `uv.lock`: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-logging`
- `tests/conftest.py` (new), `tests/test_telemetry.py` (new)
- `AGENTS.md` (human-approved)
- GitHub: #7 body edited (grooming and decisions), plus Engineer and QA comments

Commits: `edcb0bc`, `f8606c4`, `f48ecd9` (issue work) and `4c154cd` (AGENTS.md).

## Mismatches with the spec or design docs

- Q2 lists three resource attributes, then says "Both are set by env vars". It means environment and version; `service.name` is fixed in code. This is only a wording issue.
- The baseline table and fixed interfaces write `/api/orders/{id}`, while Q2 and the code use the template `/api/orders/{order_id}`. #7 uses `{order_id}`.

## Commands to validate

- **Verify:** `make verify` (19 passed; one expected WARN "fixtures changed: tests/conftest.py" for the new file)
- **Run:** `make run`, then `curl -i http://localhost:8000/api/orders/standard-1001` (and `standard-1002`, `express-1002`, `/nope`)
- **Logs:** `make logs`. Search for `http.server.request.duration` and `http.route`
- **Stop:** `make stop`

## Proposed AGENTS.md changes

Applied with human approval in `4c154cd`: the layout now lists `app/telemetry.py` and `tests/conftest.py`, and a new gotcha covers the telemetry env vars and the in-memory test providers.

## Unrelated problems noticed but not fixed

- None in product code. Test gap from QA: the log-correlation test compares trace IDs but only checks that the span ID is non-zero. The live check showed the span IDs match.

## Follow-ups for the next session

- Next issue: #8 (Q3 telemetry pipeline). It can make the console export optional and switch to OTLP.
- The cumulative metric is printed again every 5 s in `make logs`. Consider delta temporality or turning console export off when #8 lands.
- `get_order` also runs for POST and PATCH, so those requests write an `order lookup` log record too.
- The `express-1002` 500 is still present on purpose (fixed in #11).

## Suggested commit message

```
Add session summary for issue #007

Record the Q2 OpenTelemetry console-export work: PM grooming and the
human's env var decisions, the implementation, QA PASS, the approved
AGENTS.md update, and where to find the request metric in make logs.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```
