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
