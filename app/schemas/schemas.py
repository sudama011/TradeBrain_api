"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SignalBase(BaseModel):
    """Base schema for Signal model."""

    ticker: str = Field(..., min_length=1, max_length=20, description="Stock ticker symbol")
    action: str = Field(..., pattern="^(BUY|SELL|HOLD)$", description="Trading action")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score (0-100)")
    entry_price: float = Field(..., gt=0, description="Entry price for the trade")
    target_price: float = Field(..., gt=0, description="Target price for profit")
    stop_loss: float = Field(..., gt=0, description="Stop loss price")
    reasoning: str = Field(..., min_length=10, description="AI reasoning for the signal")
    source_url: Optional[str] = Field(None, description="Source URL for the signal")


class SignalCreate(SignalBase):
    """Schema for creating a new signal."""

    pass


class SignalUpdate(BaseModel):
    """Schema for updating a signal."""

    ticker: Optional[str] = Field(None, min_length=1, max_length=20)
    action: Optional[str] = Field(None, pattern="^(BUY|SELL|HOLD)$")
    confidence: Optional[int] = Field(None, ge=0, le=100)
    entry_price: Optional[float] = Field(None, gt=0)
    target_price: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = Field(None, gt=0)
    reasoning: Optional[str] = Field(None, min_length=10)
    source_url: Optional[str] = None


class SignalResponse(SignalBase):
    """Schema for signal response."""

    id: int = Field(..., description="Signal ID")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True  # For SQLAlchemy compatibility


class SignalListResponse(BaseModel):
    """Schema for list of signals response."""

    status: str = Field(..., description="Response status")
    count: int = Field(..., ge=0, description="Number of signals returned")
    data: list[SignalResponse] = Field(..., description="List of signals")
