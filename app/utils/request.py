"""
HTTP Request utilities.
Helpers for extracting IP addresses, tokens, and logging context.
"""

from typing import Any, Dict, Optional

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Get client IP address from request, considering proxies."""
    # Check for forwarded headers (proxy/load balancer)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, first one is the client
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    # Check for Cloudflare connecting IP
    cf_connecting_ip = request.headers.get("cf-connecting-ip")
    if cf_connecting_ip:
        return cf_connecting_ip.strip()

    # Fallback to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


def extract_bearer_token(request: Request) -> Optional[str]:
    """Extract bearer token from Authorization header."""
    authorization = request.headers.get("authorization")
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]
    return token if token else None


def get_request_size(request: Request) -> int:
    """Get approximate request size in bytes."""
    size = 0

    # Add URL size
    size += len(str(request.url))

    # Add headers size
    for name, value in request.headers.items():
        size += len(name) + len(value) + 4  # +4 for ": " and "\r\n"

    # Add content length if available
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size += int(content_length)
        except ValueError:
            pass

    return size


def get_request_context(request: Request) -> Dict[str, Any]:
    """Get essential request context for logging."""
    return {
        "method": request.method,
        "path": request.url.path,
        "client_ip": get_client_ip(request),
        "query_params": dict(request.query_params) if request.query_params else None,
    }
