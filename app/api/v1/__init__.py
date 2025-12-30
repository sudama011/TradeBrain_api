"""
API Version 1 package.

Contains all version 1 API endpoints and routers.
"""

from fastapi import APIRouter

from app.api.v1 import signals

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(signals.router, tags=["Signals"])
