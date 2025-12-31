from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, handle_exceptions
from app.core.logging import get_logger
from app.models import Signal
from app.repositories.signal_repository import signal_repository
from app.schemas import PaginatedResponse, PaginationParams, SignalCreate, SignalResponse, SignalUpdate

logger = get_logger(__name__)


class SignalService:
    def __init__(self, signal_repository=signal_repository):
        self.signal_repository = signal_repository

    @handle_exceptions(operation_type="signal_service")
    async def get_signals(
        self,
        session: AsyncSession,
        pagination: PaginationParams,
        ticker: Optional[str] = None,
        action: Optional[str] = None,
        min_confidence: Optional[int] = None,
        days_old: Optional[int] = None,
    ) -> PaginatedResponse[SignalResponse]:
        """
        Get paginated list of signals with optional filters.

        Args:
            session: Database session
            pagination: Pagination parameters
            ticker: Filter by ticker symbol (e.g., 'TATASTEEL')
            action: Filter by action type (BUY, SELL, HOLD)
            min_confidence: Filter by minimum confidence score (0-100)
            days_old: Filter by signals created within the last N days
        """
        response = await self.signal_repository.get_paginated_signals(
            session=session,
            pagination=pagination,
            ticker=ticker,
            action=action,
            min_confidence=min_confidence,
            days_old=days_old,
        )

        response.items = [SignalResponse.model_validate(signal, from_attributes=True) for signal in response.items]

        logger.info(
            "fetched_signals",
            count=len(response.items),
            page=pagination.page,
            size=pagination.size,
            ticker=ticker,
            action=action,
            min_confidence=min_confidence,
            days_old=days_old,
        )

        return response

    @handle_exceptions(operation_type="signal_service")
    async def get_latest_signals(
        self,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[SignalResponse]:
        """Get the latest signals."""
        signals = await self.signal_repository.get_latest_signals(session, limit)
        return [SignalResponse.model_validate(signal, from_attributes=True) for signal in signals]

    @handle_exceptions(operation_type="signal_service")
    async def get_signal_by_id(
        self,
        signal_id: UUID,
        session: AsyncSession,
    ) -> SignalResponse:
        """Get a specific signal by ID."""
        signal = await self.signal_repository.get_by_id(signal_id, session)
        if not signal:
            raise NotFoundError("Signal", str(signal_id))
        return SignalResponse.model_validate(signal, from_attributes=True)

    @handle_exceptions(operation_type="signal_service")
    async def get_signals_by_ticker(
        self,
        ticker: str,
        session: AsyncSession,
        limit: int = 50,
    ) -> List[SignalResponse]:
        """Get signals for a specific ticker."""
        signals = await self.signal_repository.get_by_ticker(ticker, session, limit)
        return [SignalResponse.model_validate(signal, from_attributes=True) for signal in signals]

    @handle_exceptions(operation_type="signal_service")
    async def get_high_confidence_signals(
        self,
        session: AsyncSession,
        min_confidence: int = 75,
        limit: int = 50,
    ) -> List[SignalResponse]:
        """Get signals with high confidence scores."""
        signals = await self.signal_repository.get_high_confidence_signals(session, min_confidence, limit)
        return [SignalResponse.model_validate(signal, from_attributes=True) for signal in signals]

    @handle_exceptions(operation_type="signal_service")
    async def create_signal(
        self,
        signal_data: SignalCreate,
        session: AsyncSession,
    ) -> SignalResponse:
        """Create a new signal."""
        signal = Signal(**signal_data.model_dump())
        created_signal = await self.signal_repository.create(signal, session)

        logger.info(
            "signal_created",
            signal_id=str(created_signal.id),
            ticker=created_signal.ticker,
            action=created_signal.action,
        )

        return SignalResponse.model_validate(created_signal, from_attributes=True)

    @handle_exceptions(operation_type="signal_service")
    async def update_signal(
        self,
        signal_id: UUID,
        signal_data: SignalUpdate,
        session: AsyncSession,
    ) -> SignalResponse:
        """Update an existing signal."""
        signal = await self.signal_repository.get_by_id(signal_id, session)
        if not signal:
            raise NotFoundError("Signal", str(signal_id))

        update_data = signal_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(signal, field, value)

        updated_signal = await self.signal_repository.update(signal, session)

        logger.info("signal_updated", signal_id=str(signal_id))

        return SignalResponse.model_validate(updated_signal, from_attributes=True)

    @handle_exceptions(operation_type="signal_service")
    async def delete_signal(
        self,
        signal_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete a signal."""
        deleted = await self.signal_repository.delete(signal_id, session)
        if not deleted:
            raise NotFoundError("Signal", str(signal_id))

        logger.info("signal_deleted", signal_id=str(signal_id))
        return True


signal_service = SignalService()
