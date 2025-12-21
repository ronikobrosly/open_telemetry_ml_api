import logging
import json
from opentelemetry import trace
from opentelemetry.trace import format_trace_id, format_span_id
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

class OtelFormatter(logging.Formatter):
    """JSON formatter that includes OpenTelemetry trace context"""

    def format(self, record):
        span = trace.get_current_span()
        span_context = span.get_span_context()

        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": format_trace_id(span_context.trace_id) if span_context.is_valid else None,
            "span_id": format_span_id(span_context.span_id) if span_context.is_valid else None,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "created", "filename", "funcName",
                          "levelname", "levelno", "lineno", "module", "msecs",
                          "message", "pathname", "process", "processName",
                          "relativeCreated", "thread", "threadName", "exc_info",
                          "exc_text", "stack_info"]:
                log_data[key] = value

        return json.dumps(log_data)

def setup_logging(level=logging.INFO, enable_otlp_export=True, otlp_endpoint=None, service_name=None, service_version=None):
    """
    Setup structured logging with OTel context and OTLP export to SigNoz

    Args:
        level: Logging level (default: INFO)
        enable_otlp_export: If True, export logs to SigNoz via OTLP (default: True)
        otlp_endpoint: OTLP endpoint (default: read from settings)
        service_name: Service name for resource (default: read from settings)
        service_version: Service version for resource (default: read from settings)
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(OtelFormatter())
    root_logger.addHandler(console_handler)

    # OTLP handler for sending logs to SigNoz
    if enable_otlp_export:
        # Import here to avoid circular dependency
        from app.core.config import settings

        endpoint = otlp_endpoint or settings.otel_exporter_otlp_endpoint
        svc_name = service_name or settings.otel_service_name
        svc_version = service_version or settings.otel_service_version

        # Create resource with service information
        resource = Resource(attributes={
            SERVICE_NAME: svc_name,
            SERVICE_VERSION: svc_version,
            "deployment.environment": settings.otel_deployment_environment,
        })

        # Create OTLP log exporter
        otlp_log_exporter = OTLPLogExporter(
            endpoint=endpoint,
            insecure=True  # Set to False if using TLS
        )

        # Create logger provider with batch processor
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(otlp_log_exporter)
        )
        set_logger_provider(logger_provider)

        # Add OTLP logging handler
        otlp_handler = LoggingHandler(
            level=level,
            logger_provider=logger_provider
        )
        root_logger.addHandler(otlp_handler)
