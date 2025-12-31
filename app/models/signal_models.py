# app/models/signal_models.py

import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel
from app.models.enums import SetupType, SignalAction, SignalStatus, UserTradeStatus


class Signal(BaseModel):
    __tablename__ = "signals"

    ticker = Column(String(20), index=True, nullable=False)
    action = Column(Enum(SignalAction), default=SignalAction.BUY, nullable=False)
    confidence = Column(Integer, nullable=False)

    status = Column(Enum(SignalStatus), default=SignalStatus.ACTIVE, nullable=False, index=True)
    setup_type = Column(Enum(SetupType), nullable=True)

    time_horizon = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)

    risk_reward = Column(Float, nullable=True)

    reasoning = Column(Text, nullable=False)
    source_url = Column(String, nullable=True)
    favorites = relationship("UserSignalFavorite", back_populates="signal", cascade="all, delete-orphan")


class UserSignalFavorite(BaseModel):
    """
    Tracks which signals a user has 'Liked' or 'Saved'.
    """

    __tablename__ = "user_signal_favorites"
    __table_args__ = (UniqueConstraint("user_id", "signal_id", name="_user_signal_uc"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    signal_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("signals.id"), nullable=False, index=True)

    signal = relationship("Signal", back_populates="favorites")
    user = relationship("User", back_populates="favorites")


class UserTrade(BaseModel):
    """
    Tracks a 'Paper Trade' or actual trade taken by the user based on a Signal.
    """

    __tablename__ = "user_trades"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False, index=True)
    signal_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("signals.id"), nullable=False, index=True)

    entry_price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)

    status = Column(Enum(UserTradeStatus), default=UserTradeStatus.OPEN, nullable=False)

    exit_price = Column(Float, nullable=True)
    pnl_amount = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)

    closed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="trades")
    signal = relationship("Signal")


class WatchlistItem(BaseModel):
    __tablename__ = "watchlist_items"

    ticker = Column(String(20), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)
    notes = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<WatchlistItem(ticker={self.ticker}, active={self.is_active})>"
