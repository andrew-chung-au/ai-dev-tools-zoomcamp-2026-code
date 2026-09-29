"""Where telemetry goes: console (on by default) and OTLP to the Collector (when an endpoint is set)."""

import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from opentelemetry._logs import LogRecord
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs.export import ConsoleLogRecordExporter
from opentelemetry.sdk.metrics.export import AggregationTemporality, ConsoleMetricExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

from app import telemetry

ENDPOINT_VARS = ("OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_CONSOLE_EXPORT")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENDPOINT_VARS:
        monkeypatch.delenv(name, raising=False)


def kinds(exporters):
    return [type(exporter) for exporter in exporters]


def test_console_only_by_default():
    assert telemetry.console_export_enabled()
    assert not telemetry.otlp_export_enabled()
    assert kinds(telemetry.span_exporters()) == [ConsoleSpanExporter]
    assert kinds(telemetry.log_exporters()) == [ConsoleLogRecordExporter]
    assert kinds(telemetry.metric_exporters()) == [ConsoleMetricExporter]


@pytest.mark.parametrize("value", ["true", "TRUE", "1", ""])
def test_console_export_stays_on_unless_false(monkeypatch, value):
    monkeypatch.setenv("OTEL_CONSOLE_EXPORT", value)
    assert telemetry.console_export_enabled()


@pytest.mark.parametrize("value", ["false", "False", " false "])
def test_console_export_can_be_turned_off(monkeypatch, value):
    monkeypatch.setenv("OTEL_CONSOLE_EXPORT", value)
    assert not telemetry.console_export_enabled()
    assert telemetry.span_exporters() == []
    assert telemetry.log_exporters() == []
    assert telemetry.metric_exporters() == []


def test_otlp_exports_all_three_signals_to_the_endpoint(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")

    assert kinds(telemetry.span_exporters()) == [ConsoleSpanExporter, OTLPSpanExporter]
    assert kinds(telemetry.log_exporters()) == [ConsoleLogRecordExporter, OTLPLogExporter]
    assert kinds(telemetry.metric_exporters()) == [ConsoleMetricExporter, OTLPMetricExporter]
    assert telemetry.span_exporters()[-1]._endpoint == "http://otel-collector:4318/v1/traces"
    assert telemetry.log_exporters()[-1]._endpoint == "http://otel-collector:4318/v1/logs"
    assert telemetry.metric_exporters()[-1]._endpoint == "http://otel-collector:4318/v1/metrics"


def test_otlp_runs_with_console_off(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
    monkeypatch.setenv("OTEL_CONSOLE_EXPORT", "false")

    assert kinds(telemetry.span_exporters()) == [OTLPSpanExporter]
    assert kinds(telemetry.log_exporters()) == [OTLPLogExporter]
    assert kinds(telemetry.metric_exporters()) == [OTLPMetricExporter]


def test_otlp_metrics_stay_cumulative(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_METRICS_TEMPORALITY_PREFERENCE", "delta")

    [exporter] = [e for e in telemetry.metric_exporters() if isinstance(e, OTLPMetricExporter)]

    assert set(exporter._preferred_temporality.values()) == {AggregationTemporality.CUMULATIVE}


class SlowCollector(BaseHTTPRequestHandler):
    """Accepts OTLP posts, but only after a delay."""

    delay = 1.0

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        time.sleep(self.delay)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture
def slow_collector():
    server = ThreadingHTTPServer(("127.0.0.1", 0), SlowCollector)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_a_slow_collector_never_blocks_the_caller(monkeypatch, slow_collector):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", slow_collector)
    monkeypatch.setenv("OTEL_CONSOLE_EXPORT", "false")
    resource = telemetry.build_resource()
    tracer_provider = telemetry.build_tracer_provider(resource)
    logger_provider = telemetry.build_logger_provider(resource)
    meter_provider = telemetry.build_meter_provider(resource)
    counter = meter_provider.get_meter("test").create_counter("test.requests")

    try:
        started = time.monotonic()
        for _ in range(20):
            with tracer_provider.get_tracer("test").start_as_current_span("lookup"):
                logger_provider.get_logger("test").emit(LogRecord(body="order lookup"))
                counter.add(1)
        assert time.monotonic() - started < 0.5
    finally:
        # Flush while the collector is still up, so nothing is left to export at exit.
        tracer_provider.shutdown()
        logger_provider.shutdown()
        meter_provider.shutdown()
