"""
Scanner scheduler for automated market scans.

Uses APScheduler to run scans on a configurable cron schedule.
"""

import asyncio
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScannerScheduler:
    """
    Manages scheduled scanner jobs using APScheduler.

    The scheduler runs scans automatically based on a cron expression.
    Default schedule: 9 AM and 3 PM on weekdays (market hours).
    """

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._is_running and self._scheduler is not None

    def start(self) -> bool:
        """
        Start the scheduler if scanner is enabled.

        Returns:
            True if scheduler started, False if disabled or already running.
        """
        if not settings.SCANNER_ENABLED:
            logger.info("scanner_scheduler_disabled")
            return False

        if self._is_running:
            logger.warning("scanner_scheduler_already_running")
            return False

        self._scheduler = AsyncIOScheduler()

        # Parse cron expression (format: minute hour day month day_of_week)
        cron_parts = settings.SCANNER_CRON_EXPRESSION.split()
        if len(cron_parts) == 5:
            trigger = CronTrigger(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day=cron_parts[2],
                month=cron_parts[3],
                day_of_week=cron_parts[4],
            )
        else:
            # Default fallback: every hour during market hours on weekdays
            trigger = CronTrigger(minute=0, hour="9-16", day_of_week="mon-fri")
            logger.warning("invalid_cron_expression_using_default", expression=settings.SCANNER_CRON_EXPRESSION)

        self._scheduler.add_job(
            self._run_scheduled_scan,
            trigger=trigger,
            id="market_scanner",
            name="Market Scanner Job",
            replace_existing=True,
        )

        self._scheduler.start()
        self._is_running = True

        logger.info(
            "scanner_scheduler_started",
            cron=settings.SCANNER_CRON_EXPRESSION,
            min_confidence=settings.SCANNER_MIN_CONFIDENCE,
        )
        return True

    def stop(self) -> None:
        """Stop the scheduler."""
        if self._scheduler and self._is_running:
            self._scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("scanner_scheduler_stopped")

    async def _run_scheduled_scan(self) -> None:
        """Execute a scheduled scan."""
        from app.scanner.scanner_service import scanner_service

        logger.info("scheduled_scan_starting")

        try:
            results = await scanner_service.run_scan(min_confidence=settings.SCANNER_MIN_CONFIDENCE)

            signals_found = sum(1 for r in results if r.success and r.action)
            errors = sum(1 for r in results if not r.success)

            logger.info(
                "scheduled_scan_completed",
                tickers_scanned=len(results),
                signals_found=signals_found,
                errors=errors,
            )
        except Exception as e:
            logger.error("scheduled_scan_failed", error=str(e))

    def get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time."""
        if not self._scheduler or not self._is_running:
            return None

        job = self._scheduler.get_job("market_scanner")
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None

    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "enabled": settings.SCANNER_ENABLED,
            "running": self._is_running,
            "cron_expression": settings.SCANNER_CRON_EXPRESSION,
            "min_confidence": settings.SCANNER_MIN_CONFIDENCE,
            "next_run_time": self.get_next_run_time(),
        }


# Singleton instance
scanner_scheduler = ScannerScheduler()
