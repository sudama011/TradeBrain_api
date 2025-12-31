"""
API Version 1 package.

Contains all version 1 API endpoints and routers.
"""

from fastapi import APIRouter

from app.api.v1 import auth, health, scanner, signals

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(signals.router, tags=["Signals"])
api_router.include_router(scanner.router, tags=["Scanner"])
