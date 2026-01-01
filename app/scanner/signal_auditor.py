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
        """
        Audits a single signal using High/Low/Close data.
        """
        try:
            # 1. Check Timeouts (Cheapest check first)
            if signal.expires_at and datetime.now(timezone.utc) > signal.expires_at:
                signal.status = SignalStatus.TIMED_OUT
                await session.merge(signal)
                await session.commit()
                stats["timeouts"] += 1
                logger.info("signal_timed_out", ticker=signal.ticker)
                return

            # 2. Fetch Live Market Data
            market_data = get_market_data(signal.ticker)
            if not market_data:
                return

            # Extract OHLC data (fallback to current_price if high/low missing)
            cmp = market_data.get("current_price")
            day_high = market_data.get("day_high", cmp)
            day_low = market_data.get("day_low", cmp)

            outcome = None

            # --- CASE A: PENDING SIGNALS (Waiting for Entry) ---
            if signal.status == SignalStatus.PENDING:
                triggered = False

                if signal.action == SignalAction.BUY:
                    # Buy Limit/Dip: Did price drop to our entry?
                    if day_low <= signal.entry_price:
                        triggered = True

                elif signal.action == SignalAction.SELL:
                    # Sell Limit/Rally: Did price rise to our entry?
                    if day_high >= signal.entry_price:
                        triggered = True

                if triggered:
                    signal.status = SignalStatus.ACTIVE
                    await session.merge(signal)
                    await session.commit()
                    stats["activated"] += 1
                    logger.info("signal_activated", ticker=signal.ticker, entry=signal.entry_price)
                return

            # --- CASE B: ACTIVE SIGNALS (Live Trade Management) ---
            if signal.status == SignalStatus.ACTIVE:

                if signal.action == SignalAction.BUY:
                    # 1. Check Stop Loss FIRST (Conservative approach)
                    if day_low <= signal.stop_loss:
                        outcome = SignalStatus.HIT_STOP_LOSS
                    # 2. Check Target
                    elif day_high >= signal.target_price:
                        outcome = SignalStatus.HIT_TARGET

                elif signal.action == SignalAction.SELL:
                    # 1. Check Stop Loss FIRST
                    if day_high >= signal.stop_loss:
                        outcome = SignalStatus.HIT_STOP_LOSS
                    # 2. Check Target
                    elif day_low <= signal.target_price:
                        outcome = SignalStatus.HIT_TARGET

                # Apply Outcome
                if outcome:
                    signal.status = outcome
                    # Optional: Record the specific price that triggered it
                    exit_price = signal.stop_loss if outcome == SignalStatus.HIT_STOP_LOSS else signal.target_price

                    await session.merge(signal)
                    await session.commit()

                    if outcome == SignalStatus.HIT_TARGET:
                        stats["wins"] += 1
                    else:
                        stats["losses"] += 1

                    logger.info("signal_closed", ticker=signal.ticker, outcome=outcome, exit_price=exit_price)

        except Exception as e:
            logger.error("audit_error", ticker=signal.ticker, error=str(e))


signal_auditor = SignalAuditor()
