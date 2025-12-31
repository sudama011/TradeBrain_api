from sqlalchemy import Boolean, Column, Enum, String

from app.models.base_models import BaseModel, UserRole


class User(BaseModel):
    """User model for authentication and authorization."""

    __tablename__ = "users"
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
