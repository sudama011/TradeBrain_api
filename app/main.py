from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import (
    AuthenticationContextMiddleware,
    ExceptionHandlerMiddleware,
    RequestResponseLoggingMiddleware,
    RequestValidationMiddleware,
    unified_exception_handler,
)
from app.core.security_constants import API_SECURITY_CONFIG
from app.db.database import close_db_connections, init_database
from app.scanner.scheduler import scanner_scheduler

# Initialize structured logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(f"Starting up {settings.APP_NAME} API...")

    await init_database(seed_data=settings.ENVIRONMENT == "dev")

    # Start the scanner scheduler for automated scans
    if scanner_scheduler.start():
        logger.info("scanner_scheduler_initialized", status=scanner_scheduler.get_status())

    logger.info("Application startup completed")

    yield

    logger.info(f"Shutting down {settings.APP_NAME} API...")
    scanner_scheduler.stop()
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
app.add_middleware(AuthenticationContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_SECURITY_CONFIG["cors_origins"],
    allow_credentials=API_SECURITY_CONFIG["allow_credentials"],
    allow_methods=API_SECURITY_CONFIG["cors_methods"],
    allow_headers=API_SECURITY_CONFIG["cors_headers"],
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
