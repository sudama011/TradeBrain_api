"""
Authentication endpoints for user login and token management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session, oauth2_scheme
from app.core.logger import get_logger
from app.schemas import LoginResponse, RefreshTokenRequest, RefreshTokenResponse
from app.services.auth import auth_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register():
    return {"message": "Registration placeholder"}


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await auth_service.authenticate_user(login_data.username, login_data.password, session)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await auth_service.refresh_token(refresh_data.refresh_token, session)


@router.post("/logout")
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict:
    return await auth_service.logout(token)


@router.post("/password-reset/request")
async def request_password_reset():
    return {"message": "Reset email sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset():
    return {"message": "Password reset successful"}
