"""
Core dependencies for FastAPI dependency injection.

Provides authentication, authorization, and database session dependencies.
"""

from typing import Annotated, Any, Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import AuthenticationError, AuthorizationError, NotFoundError, decode_token, get_logger
from app.db.database import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
logger = get_logger(__name__)


async def get_current_user_email(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    """Extract and validate user ID from JWT token."""
    try:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            raise AuthenticationError("Invalid token")

        jti = payload.get("jti")
        email = payload.get("sub")

        if not email or not jti:
            raise AuthenticationError("Invalid or expired token")

        return email
    except AuthenticationError:
        raise
    except ValueError:
        logger.warning("Invalid token format")
        raise AuthenticationError("Invalid token format")
    except Exception as e:
        logger.error("Token validation error", error=str(e))
        raise AuthenticationError("Token validation failed")


async def get_current_user(
    user_email: Annotated[str, Depends(get_current_user_email)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Optional[Any]:
    """Get current authenticated user from database."""
    try:
        # Import here to avoid circular imports
        from app.repositories.user_repository import UserRepository

        user_repository = UserRepository(None)  # Model will be set when needed
        user = await user_repository.get_by_email(user_email, session)

        if not user:
            raise NotFoundError("User", str(user_email))

        return user

    except (AuthenticationError, AuthorizationError, NotFoundError):
        raise
    except Exception:
        raise AuthenticationError("Error retrieving user information")


def require_admin(current_user: Annotated[Any, Depends(get_current_user)]) -> Any:
    """Require admin role for access."""
    # Check if user has admin attribute/role
    if not hasattr(current_user, "role") or current_user.role != "admin":
        logger.warning(
            "Admin access denied",
            user_id=str(getattr(current_user, "id", "unknown")),
        )
        raise AuthorizationError("Admin access required")
    return current_user
