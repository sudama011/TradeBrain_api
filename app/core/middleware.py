import time
import uuid
from typing import Any, Dict, Sequence

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import BaseAPIException
from app.core.logging import (
    clear_request_context,
    get_logger,
    log_api_request,
    log_api_response,
    log_security_event,
    request_id_ctx,
    user_id_ctx,
)
from app.core.security import decode_token
from app.core.security_constants import INPUT_VALIDATION_CONFIG
from app.utils import extract_bearer_token, get_client_ip, get_request_context, get_request_size

logger = get_logger(__name__)


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive request/response logging middleware.
    Generates a correlation ID and logs request/response details.
    """

    async def dispatch(self, request: Request, call_next):
        correlation_id = request_id_ctx.get()  # ExceptionHandlerMiddleware sets this
        start_time = time.time()
        request_context = get_request_context(request)
        log_api_request(**request_context)

        response = None
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = correlation_id
            return response
        finally:
            response_time = time.time() - start_time
            status_code = getattr(response, "status_code", 500)
            log_api_response(
                method=request.method,
                path=str(request.url.path),
                status_code=status_code,
                response_time=response_time,
            )
            clear_request_context()


class AuthenticationContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set user context for authenticated requests."""

    async def dispatch(self, request: Request, call_next):
        token = extract_bearer_token(request)
        if token:
            try:
                payload = decode_token(token)
                if payload and payload.get("type") == "access":
                    jti = payload.get("jti")
                    user_email = payload.get("sub")
                    user_id_ctx.set(user_email)
            except Exception:
                # If token validation fails, continue without setting user context
                # The actual authentication will be handled by dependencies
                pass

        try:
            return await call_next(request)
        finally:
            # Context will be cleared by RequestResponseLoggingMiddleware
            pass


class RequestValidationMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if not await self._validate_request_size(request):
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="Request payload too large",
            )

        return await call_next(request)

    async def _validate_request_size(self, request: Request) -> bool:
        request_size = get_request_size(request)
        if request_size and int(request_size) > INPUT_VALIDATION_CONFIG["max_request_size"]:
            log_security_event(
                event_type="request_too_large",
                description=f"Request size {request_size} exceeds limit {INPUT_VALIDATION_CONFIG["max_request_size"]}",
                client_ip=get_client_ip(request),
                path=str(request.url.path),
                method=request.method,
            )
            return False
        return True


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Global exception handler middleware."""

    async def dispatch(self, request: Request, call_next):
        try:
            correlation_id = str(uuid.uuid4())
            request_id_ctx.set(correlation_id)
            return await call_next(request)
        except Exception as exc:
            return await unified_exception_handler(request, exc)


async def unified_exception_handler(request: Request, exc: Exception):
    """
    Handles all exceptions, converting them to a unified format.
    This replaces the need for a separate ExceptionHandlerMiddleware.
    """
    correlation_id = request_id_ctx.get()

    # Handle our custom API exceptions
    if isinstance(exc, BaseAPIException):
        detail = exc.message
        status_code = exc.status_code
        error_type = exc.error_type
        logger.warning("API exception occurred", extra=exc.get_log_context())

    # Handle standard HTTP exceptions
    elif isinstance(exc, HTTPException):
        detail = exc.detail
        status_code = exc.status_code
        error_type = "http_error"
        logger.warning(
            f"HTTP exception occurred: {detail}",
            extra={
                "request_id": correlation_id,
                "path": str(request.url.path),
                "status_code": status_code,
            },
        )
    # Handle Pydantic validation errors
    elif isinstance(exc, RequestValidationError):
        formatted_errors = format_validation_error(exc.errors())
        first_error_loc = exc.errors()[0].get("loc", []) if exc.errors() else []
        error_source = first_error_loc[0] if first_error_loc else "unknown"

        if error_source == "body":
            message = "Validation failed for request body."
        elif error_source == "query":
            message = "Validation failed for query parameters."
        elif error_source == "path":
            message = "Validation failed for path parameters."
        else:
            message = "Validation failed."

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "success": False,
                "message": message,
                "error_type": "validation_error",
                "errors": formatted_errors,
            },
        )
    # Handle all other unexpected exceptions
    else:
        api_exception = BaseAPIException.from_exception(exc, "An unexpected error occurred")
        detail = api_exception.message
        status_code = api_exception.status_code
        error_type = api_exception.error_type
        logger.error(
            "Unhandled exception occurred",
            exc_info=True,
            extra={
                "request_id": correlation_id,
                "path": str(request.url.path),
                "original_exception_class": type(exc).__name__,
                **(api_exception.details or {}),
            },
        )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": detail,
            "error_type": error_type,
            "request_id": correlation_id,
        },
    )


def format_validation_error(errors: Sequence[Dict[str, Any]]) -> list:
    formatted_errors = []
    for error in errors:
        # Extract relevant fields
        loc = error.get("loc", [])
        field = loc[-1] if len(loc) > 1 else "Unknown"
        message = error.get("msg", "Validation error")
        error_type = error.get("type", "value_error")

        # Create a simpler dictionary
        formatted_errors.append(
            {
                "field": field,
                "message": message,
                "error_type": error_type,
            }
        )
    return formatted_errors
