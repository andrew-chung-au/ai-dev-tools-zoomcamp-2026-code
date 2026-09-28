"""OpenTelemetry for the Order Tracker: metrics, traces and logs, exported to the console."""

import logging
import os

# Use the stable HTTP semantic conventions, so the request metric
# (http.server.request.duration) carries http.route, the route template,
# instead of the old http.target. Must be set before instrumenting.
os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

from opentelemetry import _logs, metrics, trace  # noqa: E402
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: E402
from opentelemetry.instrumentation.logging.handler import LoggingHandler  # noqa: E402
from opentelemetry.sdk._logs import LoggerProvider  # noqa: E402
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogRecordExporter  # noqa: E402
from opentelemetry.sdk.metrics import MeterProvider  # noqa: E402
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader  # noqa: E402
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


def _configure_providers() -> None:
    """Install console-exporting SDK providers, unless SDK providers are already set (as in tests)."""
    resource = build_resource()
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(tracer_provider)
    if not isinstance(metrics.get_meter_provider(), MeterProvider):
        reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(), export_interval_millis=METRIC_EXPORT_INTERVAL_MS
        )
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
    if not isinstance(_logs.get_logger_provider(), LoggerProvider):
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(ConsoleLogRecordExporter()))
        _logs.set_logger_provider(logger_provider)


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
