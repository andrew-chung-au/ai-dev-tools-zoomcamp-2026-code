import pytest
from fastapi.testclient import TestClient
from opentelemetry.trace import SpanKind, StatusCode

from app import main, telemetry as app_telemetry

ROUTE = "/api/orders/{order_id}"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "orders.db")
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client


def server_spans(telemetry, route=ROUTE):
    return [
        span
        for span in telemetry.spans.get_finished_spans()
        if span.kind == SpanKind.SERVER and span.attributes.get("http.route") == route
    ]


@pytest.mark.parametrize(
    ("order_id", "status"),
    [("standard-1001", 200), ("standard-1002", 404), ("express-1002", 500)],
)
def test_lookup_is_recorded_with_route_template_and_status(client, telemetry, order_id, status):
    lookup = {"http.route": ROUTE, "http.request.method": "GET", "http.response.status_code": status}
    before = telemetry.request_count(**lookup)

    assert client.get(f"/api/orders/{order_id}").status_code == status

    assert telemetry.request_count(**lookup) == before + 1
    for attributes, _, _ in telemetry.request_points():
        assert order_id not in attributes.values()

    [span] = server_spans(telemetry)
    assert span.name == f"GET {ROUTE}"
    assert span.attributes["http.response.status_code"] == status


def test_metric_attributes_never_hold_the_raw_path(client, telemetry):
    client.get("/api/orders/standard-1001")
    assert client.get("/nope").status_code == 404

    for attributes, _, _ in telemetry.request_points():
        values = [str(value) for value in attributes.values()]
        assert not any("standard-1001" in value or "nope" in value for value in values)
    unmatched = [
        attributes
        for attributes, _, _ in telemetry.request_points()
        if attributes.get("http.response.status_code") == 404 and "http.route" not in attributes
    ]
    assert unmatched, "the /nope request is recorded without a route attribute"


def test_method_separates_get_from_patch_on_the_same_route(client, telemetry):
    patch = {"http.route": ROUTE, "http.request.method": "PATCH", "http.response.status_code": 200}
    before = telemetry.request_count(**patch)

    assert client.patch("/api/orders/standard-1001", json={"status": "shipped"}).status_code == 200

    assert telemetry.request_count(**patch) == before + 1


def test_server_error_span_records_the_exception(client, telemetry):
    assert client.get("/api/orders/express-1002").status_code == 500

    [span] = server_spans(telemetry)
    assert span.status.status_code == StatusCode.ERROR
    exceptions = [event for event in span.events if event.name == "exception"]
    assert exceptions and exceptions[0].attributes["exception.type"] == "ValueError"


def test_not_found_span_is_not_an_error(client, telemetry):
    assert client.get("/api/orders/standard-1002").status_code == 404

    [span] = server_spans(telemetry)
    assert span.status.status_code != StatusCode.ERROR


@pytest.mark.parametrize("order_id", ["standard-1001", "standard-1002", "express-1002"])
def test_lookup_log_carries_the_span_context(client, telemetry, order_id):
    client.get(f"/api/orders/{order_id}")

    [span] = server_spans(telemetry)
    records = [log.log_record for log in telemetry.logs.get_finished_logs()]
    lookups = [record for record in records if record.body == "order lookup"]
    assert lookups
    for record in lookups:
        assert record.attributes["order.id"] == order_id
        assert record.trace_id == span.context.trace_id
        assert record.span_id != 0
        assert record.trace_id != 0


def test_logs_hold_no_headers_or_bodies(client, telemetry):
    client.patch(
        "/api/orders/standard-1001",
        json={"status": "shipped"},
        headers={"Authorization": "Bearer secret-token"},
    )
    for log in telemetry.logs.get_finished_logs():
        text = f"{log.log_record.body} {dict(log.log_record.attributes or {})}"
        assert "secret-token" not in text
        assert "shipped" not in text


def test_all_signals_carry_the_resource(client, telemetry):
    client.get("/api/orders/standard-1001")

    [span] = server_spans(telemetry)
    [log] = [log for log in telemetry.logs.get_finished_logs() if log.log_record.body == "order lookup"]
    [(_, _, metric_resource), *_] = telemetry.request_points()
    for resource in (span.resource, log.resource, metric_resource):
        assert resource.attributes["service.name"] == "order-tracker"
        assert "deployment.environment" in resource.attributes
        assert "service.version" in resource.attributes


def test_resource_defaults_to_local(monkeypatch):
    for name in ("DEPLOYMENT_ENVIRONMENT", "SERVICE_VERSION", "ORDER_TRACKER_TAG"):
        monkeypatch.delenv(name, raising=False)

    attributes = app_telemetry.build_resource().attributes

    assert attributes["service.name"] == "order-tracker"
    assert attributes["deployment.environment"] == "local"
    assert attributes["service.version"] == "local"


def test_resource_reads_environment_and_version(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_ENVIRONMENT", "staging")
    monkeypatch.setenv("ORDER_TRACKER_TAG", "v7")
    monkeypatch.delenv("SERVICE_VERSION", raising=False)
    assert app_telemetry.build_resource().attributes["service.version"] == "v7"

    monkeypatch.setenv("SERVICE_VERSION", "1.2.3")
    attributes = app_telemetry.build_resource().attributes
    assert attributes["deployment.environment"] == "staging"
    assert attributes["service.version"] == "1.2.3"


def test_healthcheck_is_not_instrumented(client, telemetry):
    before = telemetry.request_points()

    assert client.get("/healthz").status_code == 200

    assert telemetry.spans.get_finished_spans() == ()
    assert telemetry.request_points() == before


def test_lookup_is_recorded_once_after_an_earlier_client(tmp_path, monkeypatch, telemetry):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "orders.db")
    with TestClient(main.app):
        pass
    ok = {"http.route": ROUTE, "http.request.method": "GET", "http.response.status_code": 200}
    before = telemetry.request_count(**ok)

    with TestClient(main.app) as second:
        assert second.get("/api/orders/standard-1001").status_code == 200

    assert telemetry.request_count(**ok) == before + 1
    assert len(server_spans(telemetry)) == 1
    assert (tmp_path / "orders.db").exists()
