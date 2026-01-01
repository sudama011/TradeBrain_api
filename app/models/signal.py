import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.types import SetupType, SignalAction, SignalStatus


class Signal(BaseModel):
    __tablename__ = "signals"
    __table_args__ = (CheckConstraint("ticker = UPPER(ticker)", name="ticker_is_uppercase"),)
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
