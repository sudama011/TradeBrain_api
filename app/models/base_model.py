# app/models/base_model.py

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.database import Base


class BaseModel(Base):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SystemLog(BaseModel):
    __tablename__ = "system_logs"

    level = Column(String, nullable=False)  # INFO, ERROR, CRITICAL
    source = Column(String, nullable=False)  # "Scanner", "Auditor", "Notifier"
    message = Column(Text, nullable=False)
    log_metadata = Column(JSON, nullable=True)  # Store specific error details
