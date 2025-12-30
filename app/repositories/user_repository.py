"""
User repository implementation with domain-specific operations.
Extends base repository with user-specific queries and operations.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import handle_exceptions
from app.db.query_builder import AsyncQueryBuilder
from app.models import User
from app.repositories import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    @handle_exceptions(operation_type="database")
    async def get_by_email(self, email: str, session: AsyncSession) -> Optional[User]:
        query_builder = AsyncQueryBuilder(self.model_class, session)
        return await query_builder.filter_by_fields({"email": email}).first()

    @handle_exceptions(operation_type="database")
    async def create(self, user: any, session: AsyncSession) -> User:
        """Create a new user."""
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# Singleton instance for easy import and use
user_repository = UserRepository()
