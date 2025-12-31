"""
Signal Auditor Service.

The "Truth Engine" that runs periodically to check the performance
of active signals against live market data.
"""

from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import Signal, SignalAction, SignalStatus
from app.scanner.tools import get_market_data

logger = get_logger(__name__)


class SignalAuditor:
    """
    Audits active signals to determine their outcome (WIN/LOSS/TIMEOUT).
    """

    async def audit_signals(self, session: AsyncSession) -> dict:
        """
        Main entry point: Checks all active/pending signals.
        Returns stats on how many were updated.
        """
        logger.info("signal_audit_started")

        # 1. Fetch all unresolved signals (ACTIVE or PENDING)
        query = select(Signal).where(Signal.status.in_([SignalStatus.ACTIVE, SignalStatus.PENDING]))
        result = await session.execute(query)
        signals = result.scalars().all()

        stats = {"wins": 0, "losses": 0, "timeouts": 0, "activated": 0, "processed": 0}

        for signal in signals:
            await self._audit_single_signal(signal, session, stats)
            stats["processed"] += 1

        logger.info("signal_audit_completed", stats=stats)
        return stats

    async def _audit_single_signal(self, signal: Signal, session: AsyncSession, stats: dict) -> None:
        """Audits a single signal."""
        try:
            # Check Timeouts first (cheapest check)
            if signal.expires_at and datetime.now(timezone.utc) > signal.expires_at:
                signal.status = SignalStatus.TIMED_OUT
                await session.merge(signal)
                await session.commit()
                stats["timeouts"] += 1
                logger.info("signal_timed_out", ticker=signal.ticker, id=str(signal.id))
                return

            # Fetch live price
            market_data = get_market_data(signal.ticker)
            if not market_data:
                logger.warning("audit_no_market_data", ticker=signal.ticker)
                return

            cmp = market_data.get("current_price")
            if not cmp:
                return

            # --- Logic for PENDING Signals (Waiting for Entry) ---
            if signal.status == SignalStatus.PENDING:
                # If price crossed entry, activate it
                # For BUY: If Low <= Entry <= High (approximated by CMP crossing Entry)
                # Simple logic: If CMP is now below Entry (for BUY) or above (for SELL), we triggered.
                triggered = False
                if signal.action == SignalAction.BUY and cmp <= signal.entry_price:
                    triggered = True
                elif signal.action == SignalAction.SELL and cmp >= signal.entry_price:
                    triggered = True

                if triggered:
                    signal.status = SignalStatus.ACTIVE
                    await session.merge(signal)
                    await session.commit()
                    stats["activated"] += 1
                    logger.info("signal_activated", ticker=signal.ticker, price=cmp)
                return

            # --- Logic for ACTIVE Signals (Live Trade) ---
            if signal.status == SignalStatus.ACTIVE:
                outcome = None

                if signal.action == SignalAction.BUY:
                    if cmp >= signal.target_price:
                        outcome = SignalStatus.HIT_TARGET
                    elif cmp <= signal.stop_loss:
                        outcome = SignalStatus.HIT_STOP_LOSS

                elif signal.action == SignalAction.SELL:
                    if cmp <= signal.target_price:
                        outcome = SignalStatus.HIT_TARGET
                    elif cmp >= signal.stop_loss:
                        outcome = SignalStatus.HIT_STOP_LOSS

                if outcome:
                    signal.status = outcome
                    await session.merge(signal)
                    await session.commit()

                    if outcome == SignalStatus.HIT_TARGET:
                        stats["wins"] += 1
                    else:
                        stats["losses"] += 1

                    logger.info("signal_closed", ticker=signal.ticker, outcome=outcome, close_price=cmp)

        except Exception as e:
            logger.error("audit_error", ticker=signal.ticker, error=str(e))


signal_auditor = SignalAuditor()
