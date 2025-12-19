import logging
import json
from opentelemetry import trace
from opentelemetry.trace import format_trace_id, format_span_id

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

def setup_logging(level=logging.INFO):
    """Setup structured logging with OTel context"""
    handler = logging.StreamHandler()
    handler.setFormatter(OtelFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
