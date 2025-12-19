from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Auto-instrumentation imports
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def setup_telemetry():
    """Initialize OpenTelemetry with SigNoz exporters"""

    # Define resource attributes
    resource = Resource(attributes={
        SERVICE_NAME: settings.otel_service_name,
        SERVICE_VERSION: settings.otel_service_version,
        "deployment.environment": settings.otel_deployment_environment,
        "service.namespace": "ml-demo",
    })

    # Setup Tracing
    trace_provider = TracerProvider(resource=resource)

    # Use BatchSpanProcessor for production efficiency
    otlp_span_exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True  # Set to False if using TLS
    )
    trace_provider.add_span_processor(
        BatchSpanProcessor(
            otlp_span_exporter,
            max_queue_size=2048,
            max_export_batch_size=512,
            export_timeout_millis=30000,
        )
    )
    trace.set_tracer_provider(trace_provider)

    # Setup Metrics
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True
    )
    metric_reader = PeriodicExportingMetricReader(
        otlp_metric_exporter,
        export_interval_millis=60000  # 1 minute
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(meter_provider)

    logger.info(
        "OpenTelemetry initialized",
        extra={
            "service_name": settings.otel_service_name,
            "endpoint": settings.otel_exporter_otlp_endpoint
        }
    )

def instrument_app(app):
    """Apply auto-instrumentation to FastAPI app"""

    # FastAPI auto-instrumentation
    # Note: excluded_urls can cause issues with status code reporting
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=trace.get_tracer_provider()
    )

    # httpx auto-instrumentation (for Wikipedia API)
    HTTPXClientInstrumentor().instrument()

    # SQLite3 auto-instrumentation
    SQLite3Instrumentor().instrument()

    logger.info("Auto-instrumentation applied")
