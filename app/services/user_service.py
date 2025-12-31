from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessLogicError, NotFoundError, handle_exceptions
from app.core.logging import get_logger
from app.core.security import get_password_hash
from app.models import User
from app.repositories import user_repository
from app.repositories.base_repository import RelationshipLoading
from app.schemas import PaginatedResponse, PaginationParams, UserCreate, UserResponse
from app.utils import normalize_email

logger = get_logger(__name__)


class UserService:

    def __init__(self, user_repository=user_repository):
        self.user_repository = user_repository

    @handle_exceptions(operation_type="user_service")
    async def get_user_by_email(self, email: str, session: AsyncSession) -> UserResponse:
        """Get user by email and return as UserResponse including account if present."""
        user = await self.user_repository.get_by_email(email, session)
        if user is None:
            raise NotFoundError("User not found")
        return UserResponse.model_validate(user, from_attributes=True)

    async def create_user(self, user_data: UserCreate, session: AsyncSession) -> UserResponse:
        """Create a new user."""
        user_data.email = normalize_email(user_data.email)
        existing_user = await self.user_repository.get_by_email(user_data.email, session)
        if existing_user:
            raise BusinessLogicError("User already exists")

        hashed_password = get_password_hash(user_data.password)

        # Convert to User model from UserCreate model
        user = User(
            **user_data.model_dump(exclude={"password"}),
            hashed_password=hashed_password,
        )
        created_user = await self.user_repository.create(user, session)
        return UserResponse(created_user, from_attributes=True)

    async def list_users(
        self,
        session: AsyncSession,
        pagination: PaginationParams,
    ) -> PaginatedResponse[UserResponse]:
        """Get paginated list of users as UserResponse objects."""
        relationships: RelationshipLoading = {"account": "noload"}
        response = await self.user_repository.get_paginated(
            session,
            pagination,
            relationships=relationships,
        )
        response.items = [UserResponse.model_validate(user, from_attributes=True) for user in response.items]
        return response


user_service = UserService()
