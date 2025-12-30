"""
Request and client information utilities.

Provides functions for extracting and processing HTTP request information.
"""

import re
from typing import Any, Dict, Optional

from fastapi import Request


def extract_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request."""
    return {
        "ip_address": get_client_ip(request),
        "user_agent": request.headers.get("user-agent", "unknown"),
        "referer": request.headers.get("referer", ""),
        "accept_language": request.headers.get("accept-language", ""),
        "accept_encoding": request.headers.get("accept-encoding", ""),
        "host": request.headers.get("host", ""),
        "origin": request.headers.get("origin", ""),
    }


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

    token = authorization[7:].strip()
    return token if token else None


def parse_user_agent(user_agent: str) -> Dict[str, Optional[str]]:
    """Parse user agent string to extract browser and OS information."""
    if not user_agent:
        return {
            "browser": None,
            "browser_version": None,
            "os": None,
            "device_type": None,
        }

    ua_lower = user_agent.lower()

    # Browser detection
    browser = None
    browser_version = None

    if "chrome" in ua_lower and "edg" not in ua_lower:
        browser = "Chrome"
        match = re.search(r"chrome/(\d+\.\d+)", ua_lower)
        if match:
            browser_version = match.group(1)
    elif "firefox" in ua_lower:
        browser = "Firefox"
        match = re.search(r"firefox/(\d+\.\d+)", ua_lower)
        if match:
            browser_version = match.group(1)
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
        match = re.search(r"version/(\d+\.\d+)", ua_lower)
        if match:
            browser_version = match.group(1)
    elif "edg" in ua_lower:
        browser = "Edge"
        match = re.search(r"edg/(\d+\.\d+)", ua_lower)
        if match:
            browser_version = match.group(1)
    elif "opera" in ua_lower or "opr" in ua_lower:
        browser = "Opera"
        match = re.search(r"(?:opera|opr)/(\d+\.\d+)", ua_lower)
        if match:
            browser_version = match.group(1)

    # OS detection
    os_name = None
    if "windows" in ua_lower:
        os_name = "Windows"
    elif "mac os" in ua_lower or "macos" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower:
        os_name = "Linux"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "ios" in ua_lower or "iphone" in ua_lower or "ipad" in ua_lower:
        os_name = "iOS"

    # Device type detection
    device_type = "desktop"
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        device_type = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_type = "tablet"

    return {
        "browser": browser,
        "browser_version": browser_version,
        "os": os_name,
        "device_type": device_type,
    }


def is_mobile_request(request: Request) -> bool:
    """Check if request is from mobile device."""
    user_agent = request.headers.get("user-agent", "").lower()

    mobile_indicators = [
        "mobile",
        "android",
        "iphone",
        "ipad",
        "ipod",
        "blackberry",
        "windows phone",
        "opera mini",
    ]

    return any(indicator in user_agent for indicator in mobile_indicators)


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


def extract_api_version(request: Request) -> Optional[str]:
    """Extract API version from request."""
    # Check URL path for version
    path = str(request.url.path)
    version_match = re.search(r"/v(\d+)", path)
    if version_match:
        return f"v{version_match.group(1)}"

    # Check headers
    version_header = request.headers.get("api-version")
    if version_header:
        return version_header

    # Check accept header
    accept_header = request.headers.get("accept", "")
    version_match = re.search(r"version=(\w+)", accept_header)
    if version_match:
        return version_match.group(1)

    return None


def get_request_fingerprint(request: Request) -> str:
    """Generate unique fingerprint for request."""
    import hashlib

    fingerprint_data = [
        get_client_ip(request),
        request.headers.get("user-agent", ""),
        request.headers.get("accept-language", ""),
        request.headers.get("accept-encoding", ""),
    ]

    fingerprint_string = "|".join(fingerprint_data)
    return hashlib.md5(fingerprint_string.encode()).hexdigest()


def is_bot_request(request: Request) -> bool:
    """Check if request is from a bot/crawler."""
    user_agent = request.headers.get("user-agent", "").lower()

    bot_indicators = [
        "bot",
        "crawler",
        "spider",
        "scraper",
        "curl",
        "wget",
        "python-requests",
        "postman",
        "insomnia",
        "googlebot",
        "bingbot",
        "slurp",
        "duckduckbot",
        "baiduspider",
    ]

    return any(indicator in user_agent for indicator in bot_indicators)


def get_request_context(request: Request) -> Dict[str, Any]:
    """Get comprehensive request context for logging."""
    client_info = extract_client_info(request)
    user_agent_info = parse_user_agent(client_info["user_agent"])

    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client_ip": client_info["ip_address"],
        "user_agent": client_info["user_agent"],
        "browser": user_agent_info["browser"],
        "os": user_agent_info["os"],
        "device_type": user_agent_info["device_type"],
        "is_mobile": is_mobile_request(request),
        "is_bot": is_bot_request(request),
        "api_version": extract_api_version(request),
        "request_size": get_request_size(request),
        "fingerprint": get_request_fingerprint(request),
        "referer": client_info["referer"],
        "origin": client_info["origin"],
    }
