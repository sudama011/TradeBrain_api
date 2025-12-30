import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class BaseModel(Base):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
