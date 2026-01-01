"""
Scanner service for managing the market scanner.

This service provides a unified interface for scanner operations
using the repository pattern.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.db.database import AsyncSessionLocal
from app.engine import analyze_opportunity, check_api_health, get_market_data, get_news_context
from app.models import SetupType, Signal, SignalAction, SignalStatus
from app.repositories import signal_repository, watchlist_repository

logger = get_logger(__name__)


@dataclass
class ScanResult:
    """Result of a single stock scan."""

    ticker: str
    success: bool
    action: Optional[str] = None
    confidence: Optional[int] = None
    error: Optional[str] = None


@dataclass
class ScannerStatus:
    """Current scanner status and statistics."""

    is_running: bool = False
    last_run_at: Optional[datetime] = None
    last_run_duration_seconds: Optional[float] = None
    signals_found_last_run: int = 0
    tickers_scanned_last_run: int = 0
    errors_last_run: int = 0
    last_run_results: List[Dict[str, Any]] = field(default_factory=list)


class ScannerService:
    """Service for managing the market scanner."""

    def __init__(
        self,
        watchlist_repo=watchlist_repository,
        signal_repo=signal_repository,
    ):
        self.status = ScannerStatus()
        self._lock = asyncio.Lock()
        self.watchlist_repository = watchlist_repo
        self.signal_repository = signal_repo

    async def get_watchlist(self, session: AsyncSession) -> List[str]:
        """Get the current watchlist from database."""
        return await self.watchlist_repository.get_active_tickers(session)

    async def run_scan(
        self,
        tickers: Optional[List[str]] = None,
        min_confidence: int = 75,
    ) -> List[ScanResult]:
        """
        Run a market scan for given tickers or the watchlist.

        Args:
            tickers: Optional list of tickers to scan. Uses watchlist if None.
            min_confidence: Minimum confidence score to save signals (default: 75)

        Returns:
            List of ScanResult objects with results for each ticker.
        """
        async with self._lock:
            if self.status.is_running:
                logger.warning("scan_already_running")
                return []

            self.status.is_running = True

        start_time = datetime.now(timezone.utc)
        results: List[ScanResult] = []
        signals_found = 0
        errors = 0

        try:
            async with AsyncSessionLocal() as session:
                # Get tickers from database if not provided
                scan_tickers = tickers or await self.get_watchlist(session)

                if not scan_tickers:
                    logger.warning("no_tickers_to_scan")
                    return []

                logger.info("scan_started", tickers=scan_tickers)

                for ticker in scan_tickers:
                    result = await self._scan_ticker(
                        ticker=ticker,
                        session=session,
                        min_confidence=min_confidence,
                    )
                    results.append(result)

                    if result.success and result.action:
                        signals_found += 1
                    elif not result.success:
                        errors += 1

        except Exception as e:
            logger.error("scan_failed", error=str(e))
        finally:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            self.status.is_running = False
            self.status.last_run_at = start_time
            self.status.last_run_duration_seconds = duration
            self.status.signals_found_last_run = signals_found
            self.status.tickers_scanned_last_run = len(results)
            self.status.errors_last_run = errors
            self.status.last_run_results = [
                {
                    "ticker": r.ticker,
                    "success": r.success,
                    "action": r.action,
                    "confidence": r.confidence,
                    "error": r.error,
                }
                for r in results
            ]

            logger.info(
                "scan_completed",
                duration=duration,
                signals_found=signals_found,
                errors=errors,
            )

        return results

    async def _scan_ticker(
        self,
        ticker: str,
        session: AsyncSession,
        min_confidence: int,
    ) -> ScanResult:
        """Scan a single ticker and save signal if confidence is high enough."""
        try:

            if await self.signal_repository.has_active_signal(ticker, session):
                logger.info("signal_scan_skipped_exists", ticker=ticker)
                return ScanResult(ticker=ticker, success=True, action="SKIPPED", error="Active signal already exists")

            logger.info("scanning_ticker", ticker=ticker)

            # 1. Fetch Data
            market_data = get_market_data(ticker)
            if not market_data:
                return ScanResult(ticker=ticker, success=False, error="No market data")

            news_text, source_url = get_news_context(ticker)

            # 2. Analyze (Agent + Validator)
            # This now returns a fully validated dictionary with calculated R/R and dates
            decision = analyze_opportunity(ticker, market_data, news_text)

            if not decision:
                return ScanResult(ticker=ticker, success=False, error="AI Rejected or Validation Failed")

            confidence = decision.get("confidence_score", 0)

            # 3. Save to Database
            if confidence >= min_confidence:
                signal = Signal(
                    ticker=ticker,
                    action=SignalAction(decision.get("action").upper()),
                    confidence=confidence,
                    # New Fields
                    status=SignalStatus(decision.get("status").upper()),
                    setup_type=SetupType(decision.get("setup_type").upper()),
                    time_horizon=decision.get("time_horizon"),
                    expires_at=decision.get("expires_at"),
                    risk_reward=decision.get("risk_reward"),
                    # Price Levels
                    entry_price=decision.get("entry_price"),
                    target_price=decision.get("target_price"),
                    stop_loss=decision.get("stop_loss"),
                    reasoning=decision.get("reasoning", ""),
                    source_url=source_url,
                )

                await self.signal_repository.create(signal, session)

                return ScanResult(
                    ticker=ticker,
                    success=True,
                    action=decision.get("action"),
                    confidence=confidence,
                )
            else:
                # ... existing logging ...
                return ScanResult(ticker=ticker, success=True, action=None, confidence=confidence)

        except Exception as e:
            logger.error("ticker_scan_failed", ticker=ticker, error=str(e))
            return ScanResult(ticker=ticker, success=False, error=str(e))

    async def get_status_with_watchlist(self, session: AsyncSession) -> Dict[str, Any]:
        """Get scanner status including watchlist from database."""
        watchlist = await self.get_watchlist(session)

        return {
            "is_running": self.status.is_running,
            "last_run_at": (self.status.last_run_at.isoformat() if self.status.last_run_at else None),
            "last_run_duration_seconds": self.status.last_run_duration_seconds,
            "signals_found_last_run": self.status.signals_found_last_run,
            "tickers_scanned_last_run": self.status.tickers_scanned_last_run,
            "errors_last_run": self.status.errors_last_run,
            "watchlist": watchlist,
            "last_run_results": self.status.last_run_results,
        }

    def get_status(self) -> Dict[str, Any]:
        """Get scanner status without database call (for quick checks)."""
        return {
            "is_running": self.status.is_running,
            "last_run_at": (self.status.last_run_at.isoformat() if self.status.last_run_at else None),
            "last_run_duration_seconds": self.status.last_run_duration_seconds,
            "signals_found_last_run": self.status.signals_found_last_run,
            "tickers_scanned_last_run": self.status.tickers_scanned_last_run,
            "errors_last_run": self.status.errors_last_run,
            "last_run_results": self.status.last_run_results,
        }

    def get_health(self) -> Dict[str, Any]:
        """Get scanner health status including external API health."""
        api_health = check_api_health()

        return {
            "scanner_status": "running" if self.status.is_running else "idle",
            "last_successful_run": (self.status.last_run_at.isoformat() if self.status.last_run_at else None),
            "external_apis": api_health,
        }


scanner_service = ScannerService()
