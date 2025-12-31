# app/models/user_models.py


import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base_model import BaseModel
from app.models.enums import NotificationType, PlatformType, UserRole


class User(BaseModel):
    __tablename__ = "users"
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("UserDevice", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("UserSignalFavorite", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("UserTrade", back_populates="user", cascade="all, delete-orphan")


class UserDevice(BaseModel):
    """
    Stores FCM/APNS tokens for Push Notifications.
    """

    __tablename__ = "user_devices"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)  # The FCM Token
    platform = Column(Enum(PlatformType), nullable=False)

    is_active = Column(Boolean, default=True)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="devices")


class UserSession(BaseModel):
    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String, unique=True, index=True, nullable=False)

    user_agent = Column(String, nullable=True)  # e.g., "Mozilla/5.0... iPhone"
    ip_address = Column(String, nullable=True)  # e.g., "192.168.1.5"

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="sessions")


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
