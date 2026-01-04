from uuid import UUID

from fastapi import APIRouter, status

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def take_trade():
    """'Take' a trade based on an existing signal."""
    return {"message": "Trade opened"}


@router.get("/")
async def get_trade_history(status: str = "OPEN"):
    """Fetch user's trade history."""
    return {"trades": []}


@router.patch("/{trade_id}")
async def close_trade(trade_id: UUID):
    """Close an active trade and calculate P&L."""
    return {"message": f"Trade {trade_id} closed", "pnl": 0.0}


@router.get("/stats")
async def get_trade_stats():
    """Aggregate performance data (PnL, Win Rate)."""
    return {"total_pnl": 0, "win_rate": 0.0, "open_positions": 0}
