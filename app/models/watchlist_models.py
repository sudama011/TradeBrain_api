"""
Watchlist models for tracking stocks to scan.
"""

from sqlalchemy import Boolean, Column, Integer, String

from app.models.base_models import BaseModel


class WatchlistItem(BaseModel):
    """
    Represents a stock ticker in the watchlist.

    Attributes:
        ticker: Stock symbol (e.g., "TATASTEEL", "RELIANCE")
        is_active: Whether the ticker should be included in scans
        priority: Scan priority (lower = higher priority)
        notes: Optional notes about the ticker
    """

    __tablename__ = "watchlist_items"

    ticker = Column(String(20), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    notes = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<WatchlistItem(ticker={self.ticker}, active={self.is_active})>"
