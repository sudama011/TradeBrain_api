"""
Security Policies and Rules.
"""

import re
from typing import Any, Dict, List

# API security configuration
API_SECURITY_CONFIG: Dict[str, Any] = {
    "allow_credentials": True,
    "require_https": False,  # Set to True in production
    "cors_origins": ["http://localhost:3000", "http://localhost:8000"],  # Configure based on environment
    "cors_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
    "cors_headers": ["Content-Type", "Authorization"],
    "max_request_timeout": 30,  # seconds
    "enable_request_logging": True,
    "enable_response_compression": True,
}

SUSPICIOUS_PATTERNS: List[str] = [
    # Path traversal
    "../",
    "..\\",
    # Script injection
    "<script",
    "javascript:",
    "data:",
    "vbscript:",
    # Event handlers
    "onload=",
    "onerror=",
    "onclick=",
    # Code execution
    "eval(",
    "alert(",
    "document.cookie",
    # SQL injection
    "union select",
    "drop table",
    "insert into",
    "delete from",
    # Command injection
    "exec(",
    "system(",
    "cmd.exe",
    "/bin/sh",
    # System files
    "passwd",
    "/etc/",
]

BLOCKED_USER_AGENTS: List[str] = [
    "sqlmap",
    "nikto",
    "nmap",
    "masscan",
    "zap",
    "burp",
    "acunetix",
    "nessus",
    "openvas",
    "w3af",
]

SECURITY_HEADERS: Dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'"
    ),
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "speaker=()"
    ),
}


INPUT_VALIDATION_CONFIG: Dict[str, Any] = {
    "max_string_length": 10000,
    "max_array_length": 1000,
    "max_object_depth": 10,
    "max_request_size": 10 * 1024 * 1024,  # 10MB
    "sanitize_html": True,
    "strip_whitespace": True,
    "normalize_unicode": True,
}

PASSWORD_POLICY: Dict[str, Any] = {
    "min_length": 8,
    "max_length": 72,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digits": True,
    "require_special_chars": True,
    "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    "max_consecutive_chars": 3,
    "prevent_common_passwords": True,
    "prevent_personal_info": True,
}


# Encryption configuration
ENCRYPTION_CONFIG: Dict[str, Any] = {
    "algorithm": "AES-256-GCM",
    "key_rotation_interval": 86400 * 30,  # 30 days
    "hash_algorithm": "bcrypt",
    "hash_rounds": 12,
    "token_expiry": 3600,  # 1 hour
    "refresh_token_expiry": 86400 * 7,  # 7 days
}


def get_security_pattern_regex() -> str:
    """
    Get compiled regex pattern for suspicious content detection.

    Returns:
        Regex pattern string for security scanning
    """

    # Escape special regex characters in patterns
    escaped_patterns = [re.escape(pattern) for pattern in SUSPICIOUS_PATTERNS]

    # Create alternation pattern
    return "|".join(escaped_patterns)


def is_blocked_user_agent(user_agent: str) -> bool:
    if not user_agent:
        return False
    user_agent_lower = user_agent.lower()
    return any(blocked in user_agent_lower for blocked in BLOCKED_USER_AGENTS)
