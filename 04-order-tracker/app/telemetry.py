"""OpenTelemetry for the Order Tracker: metrics, traces and logs.

Signals go to the console (only when OTEL_CONSOLE_EXPORT=true) and, when
OTEL_EXPORTER_OTLP_ENDPOINT is set, over OTLP/HTTP to the Collector. Every
exporter runs on a background thread (batch span/log processors, periodic
metric reader), so a slow or missing Collector never blocks a request.
"""

import logging
import os

# Use the stable HTTP semantic conventions, so the request metric
# (http.server.request.duration) carries http.route, the route template,
# instead of the old http.target. Must be set before instrumenting.
os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

from opentelemetry import _logs, metrics, trace  # noqa: E402
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter  # noqa: E402
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter  # noqa: E402
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # noqa: E402
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: E402
from opentelemetry.instrumentation.logging.handler import LoggingHandler  # noqa: E402
from opentelemetry.sdk._logs import LoggerProvider  # noqa: E402
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogRecordExporter  # noqa: E402
from opentelemetry.sdk.metrics import (  # noqa: E402
    Counter,
    Histogram,
    MeterProvider,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.metrics.export import (  # noqa: E402
    AggregationTemporality,
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource  # noqa: E402
from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter  # noqa: E402

SERVICE_NAME = "order-tracker"
LOGGER_NAME = "order_tracker"
METRIC_EXPORT_INTERVAL_MS = 5_000
# Regex matched against the request URL. The Compose healthcheck calls
# /healthz every 5 s; leaving it out keeps lookups readable in `make logs`.
EXCLUDED_URLS = "/healthz$"


def build_resource() -> Resource:
    """Resource attributes shared by all three signals."""
    return Resource.create(
        {
            "service.name": SERVICE_NAME,
            "deployment.environment": os.getenv("DEPLOYMENT_ENVIRONMENT") or "local",
            "service.version": os.getenv("SERVICE_VERSION") or os.getenv("ORDER_TRACKER_TAG") or "local",
        }
    )


# Prometheus needs cumulative counters; pinned so an env override can't switch to delta.
CUMULATIVE = {
    kind: AggregationTemporality.CUMULATIVE
    for kind in (Counter, UpDownCounter, Histogram, ObservableCounter, ObservableUpDownCounter, ObservableGauge)
}


def console_export_enabled() -> bool:
    """Console export is off unless OTEL_CONSOLE_EXPORT is true (unset or any other value keeps it off)."""
    return os.getenv("OTEL_CONSOLE_EXPORT", "").strip().lower() == "true"


def otlp_export_enabled() -> bool:
    """OTLP export is on when OTEL_EXPORTER_OTLP_ENDPOINT is set (compose.yaml sets it)."""
    return bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip())


def span_exporters() -> list:
    exporters = [ConsoleSpanExporter()] if console_export_enabled() else []
    if otlp_export_enabled():
        exporters.append(OTLPSpanExporter())
    return exporters


def log_exporters() -> list:
    exporters = [ConsoleLogRecordExporter()] if console_export_enabled() else []
    if otlp_export_enabled():
        exporters.append(OTLPLogExporter())
    return exporters


def metric_exporters() -> list:
    exporters = [ConsoleMetricExporter()] if console_export_enabled() else []
    if otlp_export_enabled():
        exporters.append(OTLPMetricExporter(preferred_temporality=CUMULATIVE))
    return exporters


def build_tracer_provider(resource: Resource) -> TracerProvider:
    provider = TracerProvider(resource=resource)
    for exporter in span_exporters():
        provider.add_span_processor(BatchSpanProcessor(exporter))
    return provider


def build_meter_provider(resource: Resource) -> MeterProvider:
    readers = [
        PeriodicExportingMetricReader(exporter, export_interval_millis=METRIC_EXPORT_INTERVAL_MS)
        for exporter in metric_exporters()
    ]
    return MeterProvider(resource=resource, metric_readers=readers)


def build_logger_provider(resource: Resource) -> LoggerProvider:
    provider = LoggerProvider(resource=resource)
    for exporter in log_exporters():
        provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    return provider


def _configure_providers() -> None:
    """Install exporting SDK providers, unless SDK providers are already set (as in tests)."""
    resource = build_resource()
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        trace.set_tracer_provider(build_tracer_provider(resource))
    if not isinstance(metrics.get_meter_provider(), MeterProvider):
        metrics.set_meter_provider(build_meter_provider(resource))
    if not isinstance(_logs.get_logger_provider(), LoggerProvider):
        _logs.set_logger_provider(build_logger_provider(resource))


def setup(app) -> None:
    """Configure the providers and instrument the FastAPI app. Safe to call once per app."""
    _configure_providers()
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    if not any(isinstance(handler, LoggingHandler) for handler in logger.handlers):
        logger.addHandler(LoggingHandler())
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=trace.get_tracer_provider(),
        meter_provider=metrics.get_meter_provider(),
        excluded_urls=EXCLUDED_URLS,
        exclude_spans=["receive", "send"],
    )
