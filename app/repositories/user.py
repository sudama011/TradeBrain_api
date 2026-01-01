"""
User repository implementation with domain-specific operations.
Extends base repository with user-specific queries and operations.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import handle_exceptions
from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    @handle_exceptions(operation_type="database")
    async def get_by_email(self, email: str, session: AsyncSession) -> Optional[User]:
        """Get a user by email address."""
        return await self.get_by_field("email", email, session)


# Singleton instance
user_repository = UserRepository()
