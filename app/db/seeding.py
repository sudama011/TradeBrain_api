"""
Database seeding utilities for initial data setup.

Provides functions to create initial admin user and other required data.
"""

import json
from typing import Any, Dict

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import get_password_hash
from app.models import User
from app.utils import normalize_email

logger = get_logger(__name__)

try:
    with open("app/db/mock_data.json", "r") as f:
        mock_data = json.load(f)
except FileNotFoundError:
    logger.error("mock_data.json not found. Seeding will not run.")


async def seed_database(seed: bool = True) -> None:
    if not seed or not mock_data or mock_data == {} or settings.ENVIRONMENT == "prod":
        logger.info("Seeding skipped....")
        return

    logger.info("Starting database seeding...")

    # Create a synchronous engine for the seeding script
    try:
        sync_db_url = settings.DATABASE_URL.replace("+asyncpg", "")
        sync_engine = create_engine(sync_db_url, echo=settings.DATABASE_ECHO)
    except Exception as e:
        logger.error(f"Failed to create synchronous engine: {e}")
        return

    try:
        with Session(sync_engine) as session:

            for user_data in mock_data:
                _create_user(session, user_data)

            session.commit()
            logger.info("Database seeding successful.")

    except Exception:
        raise


def _create_user(
    session: Session,
    user_data: Dict[str, Any],
) -> User:
    email = normalize_email(user_data["email"])
    existing_user = session.execute(select(User).where(User.email == email)).scalar()

    if existing_user:
        logger.info("User already exists, skipping creation.", email=email)
        return existing_user

    hashed_password = get_password_hash(user_data["password"])

    user = User(email=email, full_name=user_data["full_name"], hashed_password=hashed_password, role=user_data["role"])
    session.add(user)

    logger.info("User created successfully.", email=email)
    return user
