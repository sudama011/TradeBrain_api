from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.core.logging import get_logger
from app.schemas import PaginatedResponse, PaginationParams, SignalResponse
from app.schemas.signal_schemas import SignalCreate, SignalUpdate
from app.services import signal_service

router = APIRouter()
logger = get_logger(__name__)


@router.get("/signals", response_model=PaginatedResponse[SignalResponse])
async def get_signals(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    ticker: Optional[str] = Query(None, description="Filter by ticker symbol"),
    action: Optional[str] = Query(None, pattern="^(BUY|SELL|HOLD)$", description="Filter by action"),
    session: AsyncSession = Depends(get_session),
):
    """
    Fetches paginated trading signals with optional filters.
    """
    pagination = PaginationParams(page=page, size=size)
    return await signal_service.get_signals(
        session=session,
        pagination=pagination,
        ticker=ticker,
        action=action,
    )


@router.get("/signals/high-confidence", response_model=list[SignalResponse])
async def get_high_confidence_signals(
    min_confidence: int = Query(75, ge=0, le=100, description="Minimum confidence score"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of signals to return"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get signals with high confidence scores.
    """
    return await signal_service.get_high_confidence_signals(session, min_confidence, limit)


@router.get("/signals/ticker/{ticker}", response_model=list[SignalResponse])
async def get_signals_by_ticker(
    ticker: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of signals to return"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get signals for a specific ticker symbol.
    """
    return await signal_service.get_signals_by_ticker(ticker, session, limit)


@router.get("/signals/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific signal by ID.
    """
    return await signal_service.get_signal_by_id(signal_id, session)


@router.post("/signals", response_model=SignalResponse, status_code=201)
async def create_signal(
    signal_data: SignalCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new trading signal.
    """
    return await signal_service.create_signal(signal_data, session)


@router.patch("/signals/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: UUID,
    signal_data: SignalUpdate,
    session: AsyncSession = Depends(get_session),
):
    """
    Update an existing signal.
    """
    return await signal_service.update_signal(signal_id, signal_data, session)


@router.delete("/signals/{signal_id}", status_code=204)
async def delete_signal(
    signal_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a signal.
    """
    await signal_service.delete_signal(signal_id, session)
    return None
