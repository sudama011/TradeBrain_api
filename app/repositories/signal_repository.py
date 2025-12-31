"""
Signal repository implementation with domain-specific operations.
Extends base repository with signal-specific queries and operations.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import handle_exceptions
from app.db.query_builder import AsyncQueryBuilder
from app.models import Signal
from app.repositories.base_repository import BaseRepository
from app.schemas import PaginationParams


class SignalRepository(BaseRepository[Signal]):
    def __init__(self):
        super().__init__(Signal)

    @handle_exceptions(operation_type="database")
    async def get_by_ticker(
        self,
        ticker: str,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[Signal]:
        """Get signals for a specific ticker."""
        query_builder = AsyncQueryBuilder(self.model_class, session)
        query = (
            query_builder._build()
            .where(Signal.ticker == ticker)
            .order_by(Signal.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @handle_exceptions(operation_type="database")
    async def get_latest_signals(
        self,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[Signal]:
        """Get the latest signals ordered by creation date."""
        query_builder = AsyncQueryBuilder(self.model_class, session)
        query = query_builder._build().order_by(Signal.created_at.desc()).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    @handle_exceptions(operation_type="database")
    async def get_signals_by_action(
        self,
        action: str,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[Signal]:
        """Get signals filtered by action type (BUY, SELL, HOLD)."""
        query_builder = AsyncQueryBuilder(self.model_class, session)
        query = (
            query_builder._build()
            .where(Signal.action == action)
            .order_by(Signal.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @handle_exceptions(operation_type="database")
    async def get_high_confidence_signals(
        self,
        session: AsyncSession,
        min_confidence: int = 75,
        limit: int = 50,
    ) -> List[Signal]:
        """Get signals with confidence score above threshold."""
        query_builder = AsyncQueryBuilder(self.model_class, session)
        query = (
            query_builder._build()
            .where(Signal.confidence >= min_confidence)
            .order_by(Signal.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @handle_exceptions(operation_type="database")
    async def get_paginated_signals(
        self,
        session: AsyncSession,
        pagination: PaginationParams,
        ticker: Optional[str] = None,
        action: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated signals with optional filters."""
        query_builder = AsyncQueryBuilder(self.model_class, session)

        filters = {}
        if ticker:
            filters["ticker"] = ticker
        if action:
            filters["action"] = action

        if filters:
            query_builder = query_builder.filter_by_fields(filters)

        query_builder = query_builder.order_by_fields([("created_at", "desc")])

        return await query_builder.paginate(pagination)


# Singleton instance
signal_repository = SignalRepository()

