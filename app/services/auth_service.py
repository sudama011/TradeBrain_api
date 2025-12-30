import time
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import (
    AuthenticationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_logger,
    handle_exceptions,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas import LoginResponse, RefreshTokenResponse
from app.utils import normalize_email

logger = get_logger(__name__)


class UserAuthenticationService:
    def __init__(self):
        super().__init__()
        self.user_repository = UserRepository()

    @handle_exceptions(operation_type="auth")
    async def authenticate_user(self, email: str, password: str, session: AsyncSession) -> Dict[str, Any]:
        email = normalize_email(email)
        user = await self.user_repository.get_by_email(email, session)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        access_token = create_access_token(user.email)
        refresh_token = create_refresh_token(user.email)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user={
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            },
        )

    @handle_exceptions(operation_type="auth")
    async def refresh_token(self, refresh_token: str, session: AsyncSession) -> RefreshTokenResponse:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")
        user = await self.user_repository.get_by_email(payload.get("sub"), session)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        new_access_token = create_access_token(user.email)
        return RefreshTokenResponse(access_token=new_access_token)

    @handle_exceptions(operation_type="auth")
    async def logout(self, token: str) -> dict:
        payload = decode_token(token)
        if not payload:
            raise AuthenticationError("Invalid token")
        jti = payload.get("jti")

        if jti:
            exp = payload.get("exp")
            expires_in = exp - int(time.time()) if exp else 0
            if expires_in > 0:
                a = 10  # Placeholder for blacklisting logic
                # await blacklist_token(jti, expires_in)
        return {"message": "Successfully logged out", "success": True}


# Global service instance
auth_service = UserAuthenticationService()
