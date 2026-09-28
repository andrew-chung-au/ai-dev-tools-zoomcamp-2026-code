"""In-memory OpenTelemetry providers for tests.

Installed as the global providers before `app.main` is imported, so
`telemetry.setup()` reuses them instead of the console exporters. No
Collector or other telemetry service is needed.
"""

import pytest
from opentelemetry import _logs, metrics, trace
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import InMemoryLogRecordExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.telemetry import build_resource

_resource = build_resource()
SPANS = InMemorySpanExporter()
LOGS = InMemoryLogRecordExporter()
METRICS = InMemoryMetricReader()

_tracer_provider = TracerProvider(resource=_resource)
_tracer_provider.add_span_processor(SimpleSpanProcessor(SPANS))
trace.set_tracer_provider(_tracer_provider)

metrics.set_meter_provider(MeterProvider(resource=_resource, metric_readers=[METRICS]))

_logger_provider = LoggerProvider(resource=_resource)
_logger_provider.add_log_record_processor(SimpleLogRecordProcessor(LOGS))
_logs.set_logger_provider(_logger_provider)


class Telemetry:
    spans = SPANS
    logs = LOGS

    @staticmethod
    def request_points():
        """Data points of the HTTP server request duration histogram, as (attributes, count, resource)."""
        points = []
        data = METRICS.get_metrics_data()
        for resource_metrics in data.resource_metrics if data else []:
            for scope_metrics in resource_metrics.scope_metrics:
                for metric in scope_metrics.metrics:
                    if metric.name == "http.server.request.duration":
                        for point in metric.data.data_points:
                            points.append((dict(point.attributes), point.count, resource_metrics.resource))
        return points

    @classmethod
    def request_count(cls, **attributes):
        return sum(
            count
            for point_attributes, count, _ in cls.request_points()
            if all(point_attributes.get(key) == value for key, value in attributes.items())
        )


@pytest.fixture
def telemetry():
    SPANS.clear()
    LOGS.clear()
    return Telemetry
