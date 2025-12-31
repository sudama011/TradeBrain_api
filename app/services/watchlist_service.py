from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import WatchlistItem
from app.repositories import watchlist_repository
from app.schemas.watchlist_schemas import (
    WatchlistItemCreate,
    WatchlistItemUpdate,
    WatchlistResponse,
    WatchlistTickersResponse,
)

logger = get_logger(__name__)


class WatchlistService:

    def __init__(self, watchlist_repository=watchlist_repository):
        self.watchlist_repository = watchlist_repository

    async def get_active_tickers(self, session: AsyncSession) -> List[str]:
        """Get list of active ticker symbols for scanning."""
        tickers = await self.watchlist_repository.get_active_tickers(session)
        logger.info("fetched_active_tickers", count=len(tickers))
        return tickers

    async def get_watchlist(
        self,
        session: AsyncSession,
        include_inactive: bool = False,
    ) -> WatchlistResponse:
        """Get full watchlist with details."""
        items = await self.watchlist_repository.get_all_items(session, include_inactive)
        active_count = sum(1 for item in items if item.is_active)

        return WatchlistResponse(
            items=items,
            total=len(items),
            active_count=active_count,
        )

    async def get_tickers_only(self, session: AsyncSession) -> WatchlistTickersResponse:
        """Get just the ticker symbols."""
        tickers = await self.watchlist_repository.get_active_tickers(session)
        return WatchlistTickersResponse(watchlist=tickers, total=len(tickers))

    async def add_ticker(
        self,
        data: WatchlistItemCreate,
        session: AsyncSession,
    ) -> WatchlistItem:
        """Add a new ticker to the watchlist."""
        ticker = data.ticker.upper()

        # Check if already exists
        existing = await self.watchlist_repository.get_by_ticker(ticker, session)
        if existing:
            if not existing.is_active:
                # Reactivate if it was deactivated
                existing.is_active = True
                existing.priority = data.priority
                existing.notes = data.notes
                updated = await self.watchlist_repository.update(existing, session)
                logger.info("ticker_reactivated", ticker=ticker)
                return updated
            logger.warning("ticker_already_exists", ticker=ticker)
            return existing

        item = await self.watchlist_repository.add_ticker(
            ticker=ticker,
            session=session,
            priority=data.priority,
            notes=data.notes,
        )
        logger.info("ticker_added", ticker=ticker)
        return item

    async def remove_ticker(
        self,
        ticker: str,
        session: AsyncSession,
        hard_delete: bool = False,
    ) -> bool:
        """Remove a ticker from the watchlist."""
        ticker = ticker.upper()

        if hard_delete:
            result = await self.watchlist_repository.remove_ticker(ticker, session)
            if result:
                logger.info("ticker_deleted", ticker=ticker)
            return result
        else:
            item = await self.watchlist_repository.deactivate_ticker(ticker, session)
            if item:
                logger.info("ticker_deactivated", ticker=ticker)
                return True
            return False

    async def update_ticker(
        self,
        ticker: str,
        data: WatchlistItemUpdate,
        session: AsyncSession,
    ) -> Optional[WatchlistItem]:
        """Update a watchlist item."""
        ticker = ticker.upper()
        item = await self.watchlist_repository.get_by_ticker(ticker, session)

        if not item:
            return None

        if data.is_active is not None:
            item.is_active = data.is_active
        if data.priority is not None:
            item.priority = data.priority
        if data.notes is not None:
            item.notes = data.notes

        updated = await self.watchlist_repository.update(item, session)
        logger.info("ticker_updated", ticker=ticker)
        return updated

    async def bulk_update(
        self,
        tickers: List[str],
        session: AsyncSession,
    ) -> List[str]:
        """Replace the entire watchlist with new tickers."""
        # Deactivate all existing items
        existing_items = await self.watchlist_repository.get_all_items(session, include_inactive=True)
        for item in existing_items:
            item.is_active = False
            await self.watchlist_repository.update(item, session)

        # Add or activate the new tickers
        result_tickers = []
        for i, ticker in enumerate(tickers):
            ticker = ticker.upper()
            existing = await self.watchlist_repository.get_by_ticker(ticker, session)

            if existing:
                existing.is_active = True
                existing.priority = (i + 1) * 10  # Set priority based on order
                await self.watchlist_repository.update(existing, session)
            else:
                await self.watchlist_repository.add_ticker(
                    ticker=ticker,
                    session=session,
                    priority=(i + 1) * 10,
                )
            result_tickers.append(ticker)

        logger.info("watchlist_bulk_updated", count=len(result_tickers))
        return result_tickers


watchlist_service = WatchlistService()
