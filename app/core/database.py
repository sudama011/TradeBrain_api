from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


def _create_db_engine() -> AsyncEngine:
    """Create and configure the database engine with enhanced connection pooling."""
    try:
        if settings.DATABASE_URL.startswith("postgresql"):
            engine = create_async_engine(
                settings.DATABASE_URL,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_timeout=30,
                echo=settings.DATABASE_ECHO,
                connect_args={
                    "timeout": 10,
                    "server_settings": {
                        "application_name": f"{settings.APP_NAME}_api",
                        "timezone": "UTC",
                    },
                },
            )
            logger.info("PostgreSQL engine created.")

        else:
            engine = create_async_engine(
                settings.DATABASE_URL,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.DATABASE_ECHO,
            )
            logger.info("SQLite engine created.")

        return engine

    except Exception as e:
        logger.error("Failed to create database engine", error=str(e), exc_info=True)
        raise DatabaseError(
            "Failed to initialize database engine",
            operation="create_engine",
            original_error=str(e),
        )


# Global async engine instance
engine = _create_db_engine()

# Create Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base Model
Base = declarative_base()


# --- Dependency Injection ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Dependency: Yields an async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# --- Lifecycle Functions ---
async def init_database(seed_data: bool = False) -> None:
    """
    Initializes the database tables asynchronously.
    """
    try:
        # We use run_sync because create_all is a synchronous method
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database tables verified/created successfully.")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise e


async def close_db_connections() -> None:
    """
    Closes the database engine.
    """
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed.")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")
