from uuid import UUID

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/")
async def get_signals(ticker: str = None, action: str = None, status: str = "ACTIVE", min_confidence: int = 0):
    """Paginated trading signals feed."""
    return {"signals": [], "count": 0}


@router.get("/{signal_id}")
async def get_signal_detail(signal_id: UUID):
    """Detailed view of a specific signal."""
    return {"id": signal_id, "reasoning": "AI logic placeholder"}


@router.post("/{signal_id}/favorite")
async def favorite_signal(signal_id: UUID):
    """Save signal to favorites."""
    return {"message": f"Signal {signal_id} favorited"}


@router.delete("/{signal_id}/favorite")
async def unfavorite_signal(signal_id: UUID):
    """Remove from favorites."""
    return {"message": f"Signal {signal_id} removed from favorites"}


@router.get("/favorites")
async def get_favorite_signals():
    """Retrieve user's saved signals."""
    return {"favorites": []}


@router.patch("/{signal_id}")
async def admin_override_signal(signal_id: UUID):
    """Admin only: Manually override signal status (e.g., MANUAL_CLOSED)."""
    return {"message": f"Signal {signal_id} status updated by admin"}
