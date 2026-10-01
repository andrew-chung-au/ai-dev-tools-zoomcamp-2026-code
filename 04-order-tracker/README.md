# Order Tracker

A small order tracking app for the AI Dev Tools Zoomcamp observability homework. It includes a web page, API, tests, and a Docker Compose setup. You add telemetry, alerts, and an incident responder in Homework 4.

The main user flow is creating an order and checking its status. Three sample orders are created on first startup.

## Run it

You need Docker with Compose. To run the tests, you also need Python 3.11+ and `uv`.

```bash
docker compose up --build -d --wait
```

Open <http://127.0.0.1:8000>. The API is at `/api/orders`, and the health check is at `/healthz`. Data is stored in a Docker volume and survives container recreation.

If port 8000 is occupied, set `ORDER_TRACKER_PORT`, for example:

```bash
ORDER_TRACKER_PORT=18080 docker compose up --build -d --wait
```

Run tests with `uv run --frozen pytest -q`. Stop the stack with `make stop`, which keeps the data volumes. Run `docker compose down -v` only if you also want to delete the order and telemetry data.

## Observability stack

`make run` also starts an OpenTelemetry Collector, Prometheus, Loki, Tempo and Grafana (config in `observability/`). Every port is bound to 127.0.0.1 and can be changed with its env var:

| Service | Env var | Default | URL |
| --- | --- | --- | --- |
| App | `ORDER_TRACKER_PORT` | 8000 | <http://127.0.0.1:8000> |
| Grafana | `GRAFANA_PORT` | 3000 | <http://127.0.0.1:3000> (login `admin` / `admin`, local development only) |
| Loki (query API) | `LOKI_PORT` | 3100 | <http://127.0.0.1:3100> |
| Tempo (query API) | `TEMPO_PORT` | 3200 | <http://127.0.0.1:3200> |
| Prometheus | `PROMETHEUS_PORT` | 9090 | <http://127.0.0.1:9090> |

The Collector's OTLP ports aren't published to the host. Port 8001 is reserved for the incident responder. Console export of telemetry is off by default; `OTEL_CONSOLE_EXPORT=true make run` turns it on, so spans, metrics and logs also show up in `make logs`.

## Incident responder

`incident-response/responder.py` receives Grafana webhook alerts and hands each firing alert to a headless on-call agent (`claude -p`). It runs on the host, not in Compose. Start it from this folder (with the stack already up via `make run`), and stop it with Ctrl-C:

```bash
make responder
```

It listens on port 8001 at `POST /alerts`, answers 202 right away, and then works in the background. If port 8001 is busy, it exits with an error. Send the test alert with:

```bash
curl -X POST http://localhost:8001/alerts \
  -H 'Content-Type: application/json' \
  -d '{"alerts":[{"status":"firing","labels":{"alertname":"ResponderTest","test":"true"},"annotations":{"summary":"Test notification; no incident to fix"}}]}'
```

| Env var | Default | Purpose |
| --- | --- | --- |
| `RESPONDER_HOST` | `127.0.0.1` | Bind address. `127.0.0.0/8`, `::1` and `localhost` are loopback; anything else (including `0.0.0.0`) needs `RESPONDER_TOKEN` |
| `RESPONDER_TOKEN` | unset | Shared token, required off loopback: the responder refuses to start without it, and answers 401 to any request without `Authorization: Bearer <token>`. Not needed (and not checked) on loopback. Never logged, saved or passed to the agent |
| `RESPONDER_DRY_RUN` | unset | `1` saves incident records but doesn't run the agent |
| `RESPONDER_AGENT_TIMEOUT` | `1800` | Seconds before a running agent is stopped |
| `LOKI_URL` | `http://127.0.0.1:3100` | Loki query API. Set it when you override `LOKI_PORT` |
| `TEMPO_URL` | `http://127.0.0.1:3200` | Tempo query API. Set it when you override `TEMPO_PORT` |

`.env.example` lists `RESPONDER_HOST` and `RESPONDER_TOKEN` with placeholder values.

How alerts are handled:

- Each alert in the payload is handled by its own `status`. `resolved` alerts are skipped (one log line).
- One agent runs at a time. Up to 3 more incidents wait in a queue; a firing alert that arrives when the queue is full still gets an incident folder, marked "dropped: queue full", but no agent run.
- An alert whose `fingerprint` (or, without one, the hash of its labels) is already queued or running is a duplicate: logged, not queued again. After its agent finished, a repeat notification of the same firing (same fingerprint and `startsAt`) is also a duplicate, while a new firing is a new incident.
- `DatasourceError` and `DatasourceNoData` alerts mean the telemetry pipeline, not the app, is the likely problem: they get an incident folder with evidence but no agent run and no queue place.
- Queued incidents are held in memory and lost if the responder restarts. Ctrl-C stops a running agent too, and its incident records that it was interrupted.
- The agent runs in this folder with `incident-response/responder-task.md` and the incident folder path as its prompt. Its tools are limited to reading and editing files, `make`, `curl` to localhost and `git status`/`diff`/`add`/`commit`.

Incidents are saved in `incident-response/incidents/<UTC timestamp>-<alertname>/` (git-ignored; a numeric suffix is added when the name is taken):

| File | Contents |
| --- | --- |
| `payload.json` | The webhook body as received |
| `summary.md` | Alert name, status, affected endpoint (`endpoint` label, else `http_route`), dashboard URL (`dashboard_url` annotation), labels, annotations, alert window, evidence status and the outcome (agent finished with its exit code, agent failed/timed out, dry run, dropped, or telemetry problem). Missing values show as "unknown" |
| `logs.json` | Loki query (`{service_name="order-tracker"}`, at most 100 lines), time range and result, or why Loki couldn't be reached |
| `traces.json` | Tempo TraceQL search for 5xx spans (on the alert's route when known, at most 20 traces), time range and result, or why Tempo couldn't be reached |
| `agent-output.txt` | The agent's full output; its last line is `RESULT: <FIXED \| FALSE_POSITIVE \| ESCALATE> - ...` |
| `agent-stderr.txt` | The agent's error output |
| `agent-status.json` | Exit code, error (failed to start, timed out, interrupted) and start/finish times |

The alert window runs from the alert's `startsAt` minus its `window` label (default 5 minutes) to the time the alert arrived, at most 1 hour; without `startsAt`, the last 15 minutes. Loki and Tempo requests time out after 5 seconds.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Web page |
| GET | `/healthz` | Database health check |
| GET | `/api/orders` | List orders |
| POST | `/api/orders` | Create an order |
| GET | `/api/orders/{id}` | Check an order |
| PATCH | `/api/orders/{id}` | Change an order status |

The app uses SQLite to keep setup small. Run one app container at a time. The course exercise is about detecting and handling an incident, not scaling the database.
