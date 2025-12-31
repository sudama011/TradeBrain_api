"""
Signal repository implementation with domain-specific operations.
Extends base repository with signal-specific queries and operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import handle_exceptions
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
        """Get signals for a specific ticker, ordered by creation date."""
        return await self._get_filtered_signals(
            session=session,
            filters={"ticker": ticker.upper()},
            limit=limit,
        )

    @handle_exceptions(operation_type="database")
    async def get_latest_signals(
        self,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[Signal]:
        """Get the latest signals ordered by creation date."""
        return await self._get_filtered_signals(session=session, limit=limit)

    @handle_exceptions(operation_type="database")
    async def get_signals_by_action(
        self,
        action: str,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[Signal]:
        """Get signals filtered by action type (BUY, SELL, HOLD)."""
        return await self._get_filtered_signals(
            session=session,
            filters={"action": action.upper()},
            limit=limit,
        )

    @handle_exceptions(operation_type="database")
    async def get_high_confidence_signals(
        self,
        session: AsyncSession,
        min_confidence: int = 75,
        limit: int = 50,
    ) -> List[Signal]:
        """Get signals with confidence score above threshold."""
        return await self._get_filtered_signals(
            session=session,
            advanced_filters=[Signal.confidence >= min_confidence],
            limit=limit,
        )

    @handle_exceptions(operation_type="database")
    async def get_paginated_signals(
        self,
        session: AsyncSession,
        pagination: PaginationParams,
        ticker: Optional[str] = None,
        action: Optional[str] = None,
        min_confidence: Optional[int] = None,
        days_old: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get paginated signals with optional filters.

        Args:
            session: Database session
            pagination: Pagination parameters
            ticker: Filter by ticker symbol
            action: Filter by action type (BUY, SELL, HOLD)
            min_confidence: Filter by minimum confidence score
            days_old: Filter by signals created within the last N days
        """
        query_builder = self._get_query_builder(session)

        # Apply simple equality filters
        filters = {}
        if ticker:
            filters["ticker"] = ticker.upper()
        if action:
            filters["action"] = action.upper()

        if filters:
            query_builder = query_builder.filter_by_fields(filters)

        # Apply advanced filters (confidence and date)
        advanced_filters = []

        if min_confidence is not None:
            advanced_filters.append(Signal.confidence >= min_confidence)

        if days_old is not None:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            advanced_filters.append(Signal.created_at >= cutoff_date)

        if advanced_filters:
            query_builder = query_builder.advanced_filter(*advanced_filters)

        query_builder = query_builder.order_by_fields([("created_at", "desc")])

        return await query_builder.paginate(pagination)

    async def _get_filtered_signals(
        self,
        session: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        advanced_filters: Optional[List[Any]] = None,
        limit: int = 50,
    ) -> List[Signal]:
        """
        Internal helper to get filtered signals with common ordering.

        Args:
            session: Database session
            filters: Simple equality filters (field: value)
            advanced_filters: Complex filter expressions (e.g., >= comparisons)
            limit: Maximum number of results
        """
        query_builder = self._get_query_builder(session)

        if filters:
            query_builder = query_builder.filter_by_fields(filters)

        if advanced_filters:
            query_builder = query_builder.advanced_filter(*advanced_filters)

        query_builder = query_builder.order_by_fields([("created_at", "desc")])

        # Build and apply limit
        query = query_builder._build().limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())


# Singleton instance
signal_repository = SignalRepository()
