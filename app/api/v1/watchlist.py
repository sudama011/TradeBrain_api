from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_watchlist():
    """List tickers currently being monitored."""
    return {"watchlist": []}


@router.post("/")
async def add_to_watchlist():
    """Add a new ticker to the scanner."""
    return {"message": "Ticker added to watchlist"}


@router.delete("/{ticker}")
async def remove_from_watchlist(ticker: str):
    """Remove/Deactivate a ticker."""
    return {"message": f"Ticker {ticker} removed"}


@router.patch("/{ticker}")
async def update_watchlist_item(ticker: str):
    """Update ticker priority or notes."""
    return {"message": f"Ticker {ticker} updated"}
