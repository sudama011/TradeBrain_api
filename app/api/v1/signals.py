from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select  # Crucial import for Async V2 style

import app.models.signal as models
from app.core.database import get_db  # Import from new location
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/signals", response_model=None)
async def get_signals(limit: int = 50, db: AsyncSession = Depends(get_db)):  # Now uses AsyncSession
    """
    Fetches the latest trading signals asynchronously.
    """
    try:
        # 1. Create the Query (Select)
        query = select(models.Signal).order_by(models.Signal.created_at.desc()).limit(limit)

        # 2. Execute Async
        result = await db.execute(query)

        # 3. Convert to List (Scalars returns the objects, not rows)
        signals = result.scalars().all()

        logger.info("fetched_signals_async", count=len(signals), limit=limit)

        return {
            "status": "success",
            "count": len(signals),
            "data": signals,
        }

    except Exception as e:
        logger.error("async_db_error", error=str(e))
        raise DatabaseError(
            message="Failed to fetch signals", operation="fetch_signals_async", details={"original_error": str(e)}
        )
