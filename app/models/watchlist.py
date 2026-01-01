from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String

from app.models.base import BaseModel


class WatchlistItem(BaseModel):
    __tablename__ = "watchlist_items"
    __table_args__ = (CheckConstraint("ticker = UPPER(ticker)", name="ticker_is_uppercase"),)
    ticker = Column(String(20), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    notes = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<WatchlistItem(ticker={self.ticker}, active={self.is_active})>"
