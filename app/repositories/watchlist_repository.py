"""
Watchlist repository implementation with domain-specific operations.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import handle_exceptions
from app.models.watchlist_models import WatchlistItem
from app.repositories.base_repository import BaseRepository


class WatchlistRepository(BaseRepository[WatchlistItem]):
    """Repository for watchlist CRUD operations."""

    def __init__(self):
        super().__init__(WatchlistItem)

    @handle_exceptions(operation_type="database")
    async def get_by_ticker(
        self,
        ticker: str,
        session: AsyncSession,
    ) -> Optional[WatchlistItem]:
        """Get a watchlist item by ticker symbol."""
        return await self.get_by_field("ticker", ticker.upper(), session)

    @handle_exceptions(operation_type="database")
    async def get_active_tickers(
        self,
        session: AsyncSession,
    ) -> List[str]:
        """Get all active ticker symbols, ordered by priority."""
        # Using raw query for column projection (ticker only)
        query = (
            select(WatchlistItem.ticker)
            .where(WatchlistItem.is_active == True)  # noqa: E712
            .order_by(WatchlistItem.priority.asc())
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @handle_exceptions(operation_type="database")
    async def get_all_items(
        self,
        session: AsyncSession,
        include_inactive: bool = False,
    ) -> List[WatchlistItem]:
        """Get all watchlist items, optionally including inactive ones."""
        builder = self._get_query_builder(session)

        if not include_inactive:
            builder = builder.filter_by_fields({"is_active": True})

        return await builder.order_by_fields([("priority", "asc")]).all()

    @handle_exceptions(operation_type="database")
    async def add_ticker(
        self,
        ticker: str,
        session: AsyncSession,
        priority: int = 100,
        notes: Optional[str] = None,
    ) -> WatchlistItem:
        """Add a new ticker to the watchlist."""
        item = WatchlistItem(
            ticker=ticker.upper(),
            is_active=True,
            priority=priority,
            notes=notes,
        )
        return await self.create(item, session)

    @handle_exceptions(operation_type="database")
    async def remove_ticker(
        self,
        ticker: str,
        session: AsyncSession,
    ) -> bool:
        """Remove a ticker from the watchlist (hard delete)."""
        item = await self.get_by_ticker(ticker, session)
        if not item:
            return False
        return await self.delete(item.id, session)

    @handle_exceptions(operation_type="database")
    async def deactivate_ticker(
        self,
        ticker: str,
        session: AsyncSession,
    ) -> Optional[WatchlistItem]:
        """Deactivate a ticker (soft delete)."""
        item = await self.get_by_ticker(ticker, session)
        if not item:
            return None
        item.is_active = False
        return await self.update(item, session)

    @handle_exceptions(operation_type="database")
    async def activate_ticker(
        self,
        ticker: str,
        session: AsyncSession,
    ) -> Optional[WatchlistItem]:
        """Activate a ticker."""
        item = await self.get_by_ticker(ticker, session)
        if not item:
            return None
        item.is_active = True
        return await self.update(item, session)

    @handle_exceptions(operation_type="database")
    async def count_active(self, session: AsyncSession) -> int:
        """Count active watchlist items."""
        return await self.count(session, filters={"is_active": True})

    @handle_exceptions(operation_type="database")
    async def ticker_exists(self, ticker: str, session: AsyncSession) -> bool:
        """Check if a ticker exists in the watchlist."""
        item = await self.get_by_ticker(ticker, session)
        return item is not None


# Singleton instance
watchlist_repository = WatchlistRepository()
