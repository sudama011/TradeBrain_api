import functools
from typing import Any, Callable, Dict, Optional

from fastapi import status
from sqlalchemy.exc import DatabaseError as SQLAlchemyDatabaseError
from sqlalchemy.exc import SQLAlchemyError

from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseAPIException(Exception):
    """
    Base exception for API-specific errors.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type: str = "internal_server_error",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        **kwargs,
    ):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        self.cause = cause

        if kwargs:
            self.details.update(kwargs)

        super().__init__(self.message)

    def get_log_context(self) -> Dict[str, Any]:
        """Get sanitized context for logging."""
        from app.core.logging import sanitize_log_data

        return {
            "error_type": self.error_type,
            "status_code": self.status_code,
            "details": sanitize_log_data(self.details),
        }

    @staticmethod
    def from_exception(error: Exception, default_message: str = "An error occurred") -> "BaseAPIException":
        """
        Converts any exception to an appropriate BaseAPIException.
        Handles inheritance (e.g., catching all SQLAlchemy child errors).
        """
        if isinstance(error, BaseAPIException):
            return error

        # Check mapping with isinstance to handle subclasses (Critical Fix!)
        for error_type, exception_class in ERROR_MAPPING.items():
            if isinstance(error, error_type):
                return exception_class(message=str(error), cause=error)

        # Default fallback
        message = str(error) if str(error) else default_message
        return BaseAPIException(message, cause=error)


class ValidationError(BaseAPIException):
    """Input validation error exception."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_type="validation_error",
            details=details,
            **kwargs,
        )


class AuthenticationError(BaseAPIException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_type="authentication_error",
            **kwargs,
        )


class AuthorizationError(BaseAPIException):
    """Authorization error exception."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: str = None,
        **kwargs,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_type="authorization_error",
            required_permission=required_permission,
            **kwargs,
        )


class NotFoundError(BaseAPIException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: str = None, **kwargs):
        msg = f"{resource} not found"
        if identifier:
            msg += f": {identifier}"

        super().__init__(
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND,
            error_type="not_found",
            details={"resource": resource, "identifier": identifier},
            **kwargs,
        )


class DatabaseError(BaseAPIException):
    """Database operation error exception."""

    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="database_error",
            details={"operation": operation} if operation else None,
            **kwargs,
        )


class ExternalServiceError(BaseAPIException):
    # Fixed: Added **kwargs
    def __init__(self, service: str, error: str, **kwargs):
        super().__init__(
            message=f"{service} service failed",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_type="service_unavailable",
            details={"service": service, "original_error": str(error)},
            **kwargs,
        )


# --- Async Utilities ---


def handle_exceptions(operation_type: str = "service") -> Callable:
    """
    Async Decorator: Catches errors in async functions and converts them to API exceptions.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except BaseAPIException:
                raise
            except Exception as e:
                api_exception = BaseAPIException.from_exception(e)
                api_exception.details.update({f"{operation_type}_operation": func.__name__})
                raise api_exception

        return wrapper

    return decorator


async def safe_execute(
    operation: Callable[..., Any],
    fallback_value: Any = None,
    log_error: bool = True,
    operation_name: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """Safely execute an async operation with fallback value on error."""
    try:
        return await operation()
    except Exception as e:
        if log_error:
            op_name = operation_name or getattr(operation, "__name__", "unknown_operation")
            logger.warning(
                f"Safe execution failed for '{op_name}': {str(e)}",
                extra={
                    "operation": op_name,
                    "original_error_class": e.__class__.__name__,
                    **kwargs,
                },
            )
        return fallback_value


# --- Mappings ---

ERROR_MAPPING = {
    ValueError: ValidationError,
    PermissionError: AuthorizationError,
    FileNotFoundError: NotFoundError,
    KeyError: NotFoundError,
    SQLAlchemyError: DatabaseError,
    SQLAlchemyDatabaseError: DatabaseError,
    Exception: BaseAPIException,
}
