"""
Scanner API endpoints.

Provides endpoints for controlling the market scanner and managing watchlist.
"""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session, require_admin
from app.core.logging import get_logger
from app.models import User
from app.scanner.scheduler import scanner_scheduler
from app.schemas import WatchlistItemCreate, WatchlistItemResponse, WatchlistItemUpdate
from app.services import scanner_service, watchlist_service

router = APIRouter()
logger = get_logger(__name__)


async def run_scan_background(tickers: Optional[List[str]] = None):
    """Background task to run the scanner."""
    try:
        result = await scanner_service.run_scan(tickers)
        logger.info("background_scan_completed", results_count=len(result))
    except Exception as e:
        logger.error("background_scan_error", error=str(e))


@router.post("/scanner/run")
async def trigger_scan(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    tickers: Optional[List[str]] = Query(
        None, description="Optional list of tickers to scan. Uses watchlist if not provided."
    ),
    _admin: User = Depends(require_admin),
):
    """
    Trigger a market scan in the background.

    **Admin only:** Only administrators can trigger scans.

    This endpoint triggers the scanner to run in the background and returns immediately.
    Use GET /scanner/status to check the progress and results.

    **Parameters:**
    - `tickers`: Optional list of specific tickers to scan. If not provided, uses the database watchlist.

    **Example:** `POST /scanner/run?tickers=TATASTEEL&tickers=RELIANCE`
    """
    # Check if already running
    if scanner_service.status.is_running:
        return {
            "success": False,
            "message": "A scan is already in progress",
            "status": scanner_service.get_status(),
        }

    # Get watchlist from database if no tickers provided
    scan_tickers = tickers
    if not scan_tickers:
        scan_tickers = await watchlist_service.get_active_tickers(session)

    # Add scan to background tasks
    background_tasks.add_task(run_scan_background, scan_tickers)

    logger.info("scan_triggered", tickers=scan_tickers)

    return {
        "success": True,
        "message": "Scan started in background",
        "tickers": scan_tickers,
        "note": "Use GET /scanner/status to check progress",
    }


@router.get("/scanner/status")
async def get_scanner_status(
    session: AsyncSession = Depends(get_session),
):
    """
    Get the current scanner status.

    Returns information about:
    - Whether a scan is currently running
    - Last run timestamp
    - Number of signals found in the last run
    - Tickers scanned in the last run
    - Any errors from the last run
    - Current watchlist from database
    """
    return await scanner_service.get_status_with_watchlist(session)


@router.get("/scanner/health")
async def get_scanner_health():
    """
    Get scanner health status including external API health.

    Returns:
    - Scanner status (running/idle)
    - Last successful run timestamp
    - External API health (Tavily, yfinance)
    """
    return scanner_service.get_health()


@router.get("/scanner/watchlist")
async def get_watchlist(
    session: AsyncSession = Depends(get_session),
):
    """
    Get the current scanner watchlist from database.
    """
    return await watchlist_service.get_tickers_only(session)


@router.get("/scanner/watchlist/details")
async def get_watchlist_details(
    session: AsyncSession = Depends(get_session),
    include_inactive: bool = Query(False, description="Include inactive tickers"),
):
    """
    Get detailed watchlist information including priorities and notes.
    """
    return await watchlist_service.get_watchlist(session, include_inactive)


@router.put("/scanner/watchlist")
async def update_watchlist(
    tickers: List[str],
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_admin),
):
    """
    Replace the entire watchlist with new tickers.

    **Admin only:** Only administrators can modify the watchlist.

    **Request body:** List of ticker symbols to watch.
    """
    updated = await watchlist_service.bulk_update(tickers, session)
    return {"success": True, "watchlist": updated, "total": len(updated)}


@router.post("/scanner/watchlist", response_model=WatchlistItemResponse)
async def add_to_watchlist(
    data: WatchlistItemCreate,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_admin),
):
    """
    Add a ticker to the watchlist.

    **Admin only:** Only administrators can modify the watchlist.
    """
    item = await watchlist_service.add_ticker(data, session)
    return item


@router.patch("/scanner/watchlist/{ticker}", response_model=WatchlistItemResponse)
async def update_watchlist_item(
    ticker: str,
    data: WatchlistItemUpdate,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_admin),
):
    """
    Update a watchlist item (priority, notes, active status).

    **Admin only:** Only administrators can modify the watchlist.
    """
    item = await watchlist_service.update_ticker(ticker, data, session)
    if not item:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found in watchlist")
    return item


@router.delete("/scanner/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    session: AsyncSession = Depends(get_session),
    hard_delete: bool = Query(False, description="Permanently delete instead of deactivating"),
    _admin: User = Depends(require_admin),
):
    """
    Remove a ticker from the watchlist.

    **Admin only:** Only administrators can modify the watchlist.

    By default, this deactivates the ticker. Use `hard_delete=true` to permanently remove.
    """
    result = await watchlist_service.remove_ticker(ticker, session, hard_delete)
    if not result:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found in watchlist")
    return {"success": True, "ticker": ticker.upper(), "deleted": hard_delete}


# ==================== Scheduler Endpoints ====================


@router.get("/scanner/scheduler/status")
async def get_scheduler_status():
    """
    Get the current scheduler status.

    Returns:
    - Whether scheduling is enabled
    - Whether the scheduler is running
    - Cron expression configuration
    - Minimum confidence threshold
    - Next scheduled run time
    """
    return scanner_scheduler.get_status()


@router.post("/scanner/scheduler/start")
async def start_scheduler(
    _admin: User = Depends(require_admin),
):
    """
    Start the scheduler for automatic scans.

    **Admin only:** Only administrators can control the scheduler.

    The scheduler will run scans based on the configured cron expression.
    """
    if scanner_scheduler.is_running:
        return {"success": False, "message": "Scheduler is already running"}

    started = scanner_scheduler.start()
    if started:
        return {
            "success": True,
            "message": "Scheduler started",
            "status": scanner_scheduler.get_status(),
        }
    return {
        "success": False,
        "message": "Failed to start scheduler (may be disabled in config)",
    }


@router.post("/scanner/scheduler/stop")
async def stop_scheduler(
    _admin: User = Depends(require_admin),
):
    """
    Stop the scheduler for automatic scans.

    **Admin only:** Only administrators can control the scheduler.

    Running scans will continue, but no new scans will be scheduled.
    """
    if not scanner_scheduler.is_running:
        return {"success": False, "message": "Scheduler is not running"}

    scanner_scheduler.stop()
    return {"success": True, "message": "Scheduler stopped"}


@router.post("/scanner/scheduler/trigger")
async def trigger_scheduled_scan(
    background_tasks: BackgroundTasks,
    _admin: User = Depends(require_admin),
):
    """
    Manually trigger a scheduled scan immediately.

    **Admin only:** Only administrators can trigger scans.

    This runs the same scan that would run on schedule, using the configured
    minimum confidence threshold and the full watchlist.
    """
    if scanner_service.status.is_running:
        return {
            "success": False,
            "message": "A scan is already in progress",
            "status": scanner_service.get_status(),
        }

    # Run the scheduled scan in background
    async def run_immediate_scan():
        await scanner_scheduler._run_scheduled_scan()

    background_tasks.add_task(run_immediate_scan)
    logger.info("manual_scheduled_scan_triggered")

    return {
        "success": True,
        "message": "Scheduled scan triggered",
        "note": "Use GET /scanner/status to check progress",
    }
