import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.errors import ValidationError
from app.core.logger import get_logger
from app.core.policies import ENCRYPTION_CONFIG, PASSWORD_POLICY
from app.core.settings import settings

logger = get_logger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=ENCRYPTION_CONFIG["hash_rounds"],
    bcrypt__ident="2b",
)

PASSWORD_MIN_LENGTH = PASSWORD_POLICY["min_length"]
PASSWORD_REQUIRE_UPPERCASE = PASSWORD_POLICY["require_uppercase"]
PASSWORD_REQUIRE_LOWERCASE = PASSWORD_POLICY["require_lowercase"]
PASSWORD_REQUIRE_DIGITS = PASSWORD_POLICY["require_digits"]
PASSWORD_REQUIRE_SPECIAL = PASSWORD_POLICY["require_special_chars"]
PASSWORD_SPECIAL_CHARS = PASSWORD_POLICY["special_chars"]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    validation_result = _validate_password_strength(password)
    if not validation_result["is_valid"]:
        raise ValidationError(
            f"Password does not meet security requirements: {', '.join(validation_result['errors'])}",
            field="password",
            code="weak_password",
            strength_score=validation_result["strength_score"],
        )

    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, int],
    expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, int],
    expires_delta: timedelta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT token, returning the subject (typically email or user id)."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def _validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength according to security policy."""
    errors = []

    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")

    if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if PASSWORD_REQUIRE_SPECIAL and not any(c in PASSWORD_SPECIAL_CHARS for c in password):
        errors.append(f"Password must contain at least one special character: {PASSWORD_SPECIAL_CHARS}")

    weak_passwords = ["password", "123456", "qwerty", "admin", "letmein"]
    if password.lower() in weak_passwords:
        errors.append("Password is too common and easily guessable")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "strength_score": _calculate_password_strength(password),
    }


def _calculate_password_strength(password: str) -> int:
    """Calculate password strength score (0-100)."""
    score = 0

    score += min(25, len(password) * 2)

    if any(c.isupper() for c in password):
        score += 15
    if any(c.islower() for c in password):
        score += 15
    if any(c.isdigit() for c in password):
        score += 15
    if any(c in PASSWORD_SPECIAL_CHARS for c in password):
        score += 20

    unique_chars = len(set(password))
    if unique_chars < len(password) * 0.7:
        score -= 10

    return min(100, max(0, score))
