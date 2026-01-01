import uuid

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.types import UserTradeStatus


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
