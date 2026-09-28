# Order Tracker: Observability & Incident Response (Homework 4)

## Purpose

Order Tracker is a small FastAPI + SQLite service. It has a web page, a JSON API and three seeded orders. Homework 4 (based on "DevOps and Observability for an AI-Built App", AI Dev Tools Zoomcamp part 4) adds four things around it: OpenTelemetry instrumentation, a telemetry pipeline with a Grafana dashboard, a 5xx alert, and an automatic on-call responder. When the alert fires, the responder launches a headless coding agent to investigate and fix the incident.

A customer reports they "cannot open an order", but the website looks fine. By the end, the system detects that failure, alerts on it, and hands it to an agent with enough context to fix it.

## Existing app (baseline)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Web page |
| GET | `/healthz` | Database health check |
| GET | `/api/orders` | List orders |
| POST | `/api/orders` | Create an order |
| GET | `/api/orders/{id}` | Check an order |
| PATCH | `/api/orders/{id}` | Change an order status |

Seeded on first startup: `standard-1001`, `express-1002` (placed on the last day of the previous month), `standard-1003`. The app runs from `compose.yaml` (`make run`) on `127.0.0.1:${ORDER_TRACKER_PORT:-8000}`, with data in the `orders` volume.

## Fixed interfaces

The homework's test commands depend on these. They must not change.

1. **Order lookup route:** `GET /api/orders/{id}` on the app at `http://localhost:8000`, returning the order JSON, or 404 when the id doesn't exist. Test calls:
   - `curl -i http://localhost:8000/api/orders/standard-1001`
   - `curl -i http://localhost:8000/api/orders/standard-1002`
   - `curl -i http://localhost:8000/api/orders/express-1002`
2. **Seed data:** the three seeded orders and their ids stay as they are. `standard-1002` stays unseeded.
3. **Responder endpoint:** an HTTP service on port **8001** that accepts `POST /alerts` with a Grafana-style webhook JSON body: `{"alerts":[{"status", "labels", "annotations", ...}]}`.
4. **ResponderTest alert:** the responder must accept this exact payload and handle it end to end (store context, start the agent, record its answer):

   ```bash
   curl -X POST http://localhost:8001/alerts \
     -H 'Content-Type: application/json' \
     -d '{"alerts":[{"status":"firing","labels":{"alertname":"ResponderTest","test":"true"},"annotations":{"summary":"Test notification; no incident to fix"}}]}'
   ```

5. **Rebuild command:** `docker compose up --build -d --wait` (also `make run`), run from this folder, brings up the app **and** the observability stack and waits until they're healthy.

## Requirements by question

### Q2: Instrument order lookups
- Instrument the app with OpenTelemetry (FastAPI auto-instrumentation plus manual additions where needed): **metrics, logs and traces** for order lookups (`GET /api/orders/{id}`).
- Every signal carries resource attributes for **service name** (`order-tracker`), **environment** and **deployed version**. Both are set by env vars, defaulting to `local` and the image tag.
- The request metric has attributes for the **route** (the template `/api/orders/{order_id}`, not the raw id) and the **HTTP status code**.
- Export all three signals to the **console**, so they show up in `docker compose logs app` / `make logs`.
- Check: after a rebuild, looking up `standard-1001` produces a request metric in the app logs with its status code.

### Q3: Telemetry pipeline
- Add an **OpenTelemetry Collector, Prometheus, Loki, Tempo and Grafana**. Their config files live in `observability/`. The services join the main `compose.yaml` (for example with Compose `include:`), so the rebuild command starts everything.
- The app sends metrics, logs and traces over OTLP to the Collector. The Collector routes metrics → Prometheus, logs → Loki, traces → Tempo. Console export from Q2 may stay or become optional.
- Grafana is provisioned from files in the repo: data sources (with log ↔ trace links) plus a dashboard for **request counts and errors** by route and status, filterable by environment and version.
- All configuration is committed. Nothing is set up by hand in the UI. All ports are bound to `127.0.0.1` (the host-run responder is the one exception; see Q5).
- Check: after a rebuild and a lookup of `standard-1002`, Grafana shows the request metric, and the matching log and trace can be found.

### Q4: 5xx alert
- A provisioned Grafana alert rule on **5xx** responses from the request metric. Threshold: any 5xx on a route within a **5-minute window**. Pending period: about **1 minute**. A few failing requests should fire it.
- Labels/annotations include the **endpoint (route)**, the **time window**, **service**, **environment**, **deployed version**, **owner**, and the **dashboard URL**.
- **No-data handling:** when there are no 5xx responses (or no series at all), the alert is Normal, not No Data or Error.
- In this step the alert is only checked by its state in Grafana. The webhook comes in Q6.
- Check: re-run the `standard-1002` lookup, wait for evaluation, and read the alert state.

### Q5: Automatic responder (on-call engineer)
- New service in `incident-response/`. It runs as a host process, listening on **port 8001** and handling **`POST /alerts`**.
- The bind address comes from `RESPONDER_HOST`, default `127.0.0.1`. Grafana's container can't reach the host's loopback, so Q6 runs the responder on a non-loopback address. This is the only exception to binding to `127.0.0.1`.
- On a non-loopback address the responder requires a shared token (`RESPONDER_TOKEN`): it refuses to start without one, and rejects requests whose `Authorization` header doesn't carry it. On the default `127.0.0.1` no token is needed.
- On each firing alert, save an incident record with what's needed to understand the problem: alert name, status, labels/annotations, affected endpoint, dashboard URL, and the related logs (Loki) and traces (Tempo) for the alert window.
- Then start the coding assistant **in headless mode** (`claude -p`) in this folder, with the incident record and an on-call prompt along these lines:
  > You are the on-call engineer for this repository. An alert just fired. Investigate the root cause. Read the code and reproduce the failure. If you find a real bug, make the smallest correction, run the tests, restart the app, verify the failing request now succeeds, and commit the fix with a clear message. If the alert is a test or a false positive, explain why and do not change the code.
- Save the agent's full output with the incident.
- Respond quickly (2xx) to the webhook sender. The agent runs asynchronously, one at a time.
- Check: send the ResponderTest payload, wait for the agent to finish, and read its response (including the last line). The agent should report that there's nothing to fix and change nothing.

### Q6: End-to-end incident
- Connect the Q4 alert to the responder with a provisioned Grafana **webhook contact point** → `http://host.docker.internal:8001/alerts`, sending the responder's shared token in the `Authorization` header.
- Check: request `GET /api/orders/express-1002` (repeat if needed) → the alert fires → Grafana sends the webhook → the responder starts the agent → the agent finds and fixes the root cause, restarts the app and verifies that the same request no longer fails.
- The fix follows normal project rules: a regression test, `make verify` passes, commit to `main`, no push.

## Constraints

- **The express-1002 incident must stay unfixed until Q6.** Earlier work must not touch the express delivery-date logic in `order_detail`. No new bugs are introduced; the seeded one is the incident.
- One app container at a time (SQLite).
- Everything lives inside this folder, including `observability/` and `incident-response/`.
- New dependencies (OpenTelemetry packages, the responder's web framework) need approval before they're added.
- Tests must not require the telemetry stack to be running.

## Out of scope

- Dev/prod environments, container registries, CI/CD build/deploy/promotion workflows, cloud deployment (AWS/CloudFormation) and cloud cleanup, all of which the lesson covers.
- Business metrics beyond request counts and errors.
- Escalating to a human on-call engineer.
- Scaling, replacing SQLite, or running several app replicas.
- Alert routing other than the webhook to the responder (email, Slack, PagerDuty, SNS, etc.).
- Authentication/TLS for Grafana, the Collector or the responder (local-only stack), apart from the responder's shared token (Q5).
- Production hardening: retention, HA, persistent Grafana state beyond provisioning, running the agent in isolated container jobs.
- The responder pushing code or opening PRs.
- Changes to the web page (`static/index.html`) or the order API's behavior, apart from the Q6 fix.
