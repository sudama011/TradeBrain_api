import logging
import sys
from contextvars import ContextVar
from typing import Any, Dict, Optional

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import LoggerFactory

from app.core.config import settings

# Context variables for request correlation
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def add_core_metadata_processor(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Processor to add core service metadata to every log entry."""
    event_dict.update(
        {
            "api_version": settings.API_VERSION,
            "environment": settings.ENVIRONMENT,
        }
    )
    return event_dict


class CustomJSONRenderer(JSONRenderer):
    """
    Simplified JSON renderer that adds request correlation IDs.
    It inherits from the standard JSONRenderer for core functionality.
    """

    def __call__(self, _, __, event_dict):
        """Render log entry as JSON with correlation IDs."""
        # Add request correlation if available
        if request_id := request_id_ctx.get():
            event_dict["request_id"] = request_id

        # Pass the dictionary to the parent JSONRenderer for final serialization
        return super().__call__(_, __, event_dict)


def configure_logging() -> None:
    """Configure enhanced structured logging for production."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_core_metadata_processor,
        structlog.processors.dict_tracebacks,
    ]

    if settings.DEBUG:
        # Use simple processors and console renderer for development
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=True)]
    else:
        # Use dedicated processors and custom JSON renderer for production
        processors = shared_processors + [CustomJSONRenderer()]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    _configure_third_party_loggers()


def _configure_third_party_loggers():
    """Configure third-party library loggers."""
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger instance for this class."""
        return get_logger(self.__class__.__name__)


def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize log data to remove sensitive information."""
    sensitive_keys = {
        "password",
        "token",
        "secret",
        "key",
        "authcredential",
        "authorization",
        "cookie",
        "session",
        "csrf",
        "api_key",
        "access_token",
        "refresh_token",
        "private_key",
    }

    sanitized: Dict[str, Any] = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_log_data(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value

    return sanitized


def log_api_request(
    method: str,
    path: str,
    **kwargs,
) -> None:
    logger = get_logger("api.request")
    sanitized_kwargs = sanitize_log_data(kwargs)
    logger.info(
        "API request started",
        method=method,
        path=path,
        **sanitized_kwargs,
    )


def log_api_response(
    method: str,
    path: str,
    status_code: int,
    response_time: float,
    **kwargs,
) -> None:
    logger = get_logger("api.response")
    if status_code >= 500:
        log_level = "error"
    elif status_code >= 400:
        log_level = "warning"
    else:
        log_level = "info"

    sanitized_kwargs = sanitize_log_data(kwargs)
    performance_class = _classify_response_time(response_time)

    getattr(logger, log_level)(
        "API response completed",
        method=method,
        path=path,
        status_code=status_code,
        response_time=f"{response_time:.3f}s",
        performance_class=performance_class,
        **sanitized_kwargs,
    )


def log_security_event(
    event_type: str,
    ip_address: str = None,
    user_agent: str = None,
    **kwargs,
) -> None:
    """Log security-related events."""
    logger = get_logger("security.event")
    logger.warning(
        "Security event",
        event_type=event_type,
        ip_address=ip_address,
        user_agent=user_agent,
        **kwargs,
    )


def log_business_event(
    event_type: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """Log business events for analytics and monitoring."""
    logger = get_logger("business.event")
    logger.info(
        "Business event",
        event_type="business_event",
        business_event_type=event_type,
        description=description,
        metadata=sanitize_log_data(metadata or {}),
        **sanitize_log_data(kwargs),
    )


def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "seconds",
    context: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """Log performance metrics for monitoring."""
    logger = get_logger("performance.metric")
    logger.info(
        "Performance metric",
        event_type="performance_metric",
        metric_name=metric_name,
        metric_value=value,
        metric_unit=unit,
        context=sanitize_log_data(context or {}),
        **sanitize_log_data(kwargs),
    )


# Utility functions for easier logging
def set_request_context(request_id: str, user_id: Optional[str] = None) -> None:
    """Set request context for correlation across logs."""
    request_id_ctx.set(request_id)


def clear_request_context() -> None:
    """Clear request context."""
    request_id_ctx.set(None)


def _classify_response_time(response_time: float) -> str:
    """Classify response time for performance monitoring."""
    if response_time < 0.1:
        return "fast"
    elif response_time < 0.5:
        return "normal"
    elif response_time < 2.0:
        return "slow"
    else:
        return "very_slow"
