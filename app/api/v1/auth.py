"""
Authentication endpoints for user login and token management.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger, get_session, oauth2_scheme
from app.schemas import LoginResponse, RefreshTokenRequest, RefreshTokenResponse
from app.services.auth_service import auth_service

logger = get_logger(__name__)
router = APIRouter()


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
