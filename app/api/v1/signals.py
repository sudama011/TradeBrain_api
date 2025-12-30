from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import DatabaseError, get_logger, get_session
from app.models import Signal
from app.schemas import PaginatedResponse, SignalResponse

router = APIRouter()
logger = get_logger(__name__)


@router.get("/signals", response_model=PaginatedResponse[SignalResponse])
async def get_signals(limit: int = 50, session: AsyncSession = Depends(get_session)):
    """
    Fetches the latest trading signals asynchronously.
    """
    try:
        if limit <= 0 or limit > 1000:
            limit = 50

        query = select(Signal).order_by(Signal.created_at.desc()).limit(limit)

        result = await session.execute(query)

        signals = result.scalars().all()

        logger.info("fetched_signals_async", count=len(signals), limit=limit)

        return PaginatedResponse[SignalResponse](
            items=[SignalResponse.model_validate(signal, from_attributes=True) for signal in signals],
            total=len(signals),
            page=1,
            size=limit,
        )

    except Exception as e:
        logger.error("async_db_error", error=str(e))
        raise DatabaseError(
            message="Failed to fetch signals", operation="fetch_signals_async", details={"original_error": str(e)}
        )
