from functools import wraps
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from typing import Callable
import logging

logger = logging.getLogger(__name__)

def traced_component(component_name: str, **default_attributes):
    """Decorator to automatically create spans for component methods"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = f"{component_name}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # Add default attributes
                for key, value in default_attributes.items():
                    span.set_attribute(key, value)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    logger.error(
                        f"{span_name} failed",
                        extra={"error": str(e)},
                        exc_info=True
                    )
                    raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = f"{component_name}.{func.__name__}"

            with tracer.start_as_current_span(span_name) as span:
                # Add default attributes
                for key, value in default_attributes.items():
                    span.set_attribute(key, value)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    logger.error(
                        f"{span_name} failed",
                        extra={"error": str(e)},
                        exc_info=True
                    )
                    raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
