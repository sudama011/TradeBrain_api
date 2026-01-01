import uuid

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.types import NotificationType


class Notification(BaseModel):
    """
    In-App Notification History (The 'Bell' Icon).
    """

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.SYSTEM, nullable=False)

    is_read = Column(Boolean, default=False)

    related_signal_id = Column(Uuid, ForeignKey("signals.id"), nullable=True)

    user = relationship("User", back_populates="notifications")
