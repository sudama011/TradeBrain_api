from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import close_db_connections, init_database
from app.core.logging import configure_logging, get_logger
from app.core.middleware import (
    AuthenticationMiddleware,
    ExceptionHandlerMiddleware,
    RequestResponseLoggingMiddleware,
    RequestValidationMiddleware,
    unified_exception_handler,
)

# Initialize structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(f"Starting up {settings.APP_NAME} API...")

    await init_database(seed_data=settings.ENVIRONMENT != "production")
    logger.info("Application startup completed")

    yield

    logger.info(f"Shutting down {settings.APP_NAME} API...")
    await close_db_connections()
    logger.info("Application shutdown completed")


app = FastAPI(
    title=settings.APP_NAME,
    description="TradeBrain API - Intelligent trading signals and analytics.",
    version=settings.API_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Replace FastAPI's default exception handler.
app.add_exception_handler(HTTPException, unified_exception_handler)
app.add_exception_handler(RequestValidationError, unified_exception_handler)

# Add middleware (order matters - they execute in reverse order)
app.add_middleware(RequestResponseLoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(ExceptionHandlerMiddleware)

# Include API routers
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }
