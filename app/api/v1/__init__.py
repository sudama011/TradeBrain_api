"""
API Version 1 package.

Contains all version 1 API endpoints and routers.
"""

from fastapi import APIRouter

from app.api.v1 import admin, auth, health, notifications, signals, trades, users, watchlist

api_router = APIRouter()

# 1. Authentication & Users
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

# 2. Signals (The Feed)
api_router.include_router(signals.router, prefix="/signals", tags=["Signals"])

# 3. Portfolio (Trading)
api_router.include_router(trades.router, prefix="/trades", tags=["Trades"])

# 4. Notifications
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

# 5. Watchlist (Scanner Input)
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist"])

# 6. System & Admin
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(health.router, prefix="/health", tags=["System"])
