"""
Pydantic schemas for watchlist API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WatchlistItemCreate(BaseModel):
    """Schema for creating a new watchlist item."""

    ticker: str = Field(..., min_length=1, max_length=20, description="Stock ticker symbol")
    is_active: bool = Field(default=True, description="Whether to include in scans")
    priority: int = Field(default=100, ge=1, le=1000, description="Scan priority (lower = higher)")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional notes")


class WatchlistItemUpdate(BaseModel):
    """Schema for updating a watchlist item."""

    is_active: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=1, le=1000)
    notes: Optional[str] = Field(default=None, max_length=500)


class WatchlistItemResponse(BaseModel):
    """Schema for watchlist item response."""

    id: UUID
    ticker: str
    is_active: bool
    priority: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    """Schema for full watchlist response."""

    items: List[WatchlistItemResponse]
    total: int
    active_count: int


class WatchlistTickersResponse(BaseModel):
    """Simple response with just ticker symbols."""

    watchlist: List[str]
    total: int


class WatchlistBulkUpdate(BaseModel):
    """Schema for bulk updating the watchlist."""

    tickers: List[str] = Field(..., min_length=1, description="List of ticker symbols")
