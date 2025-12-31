"""
Signal Validator Service.

Acts as a "Math Police" to ensure AI-generated signals
adhere to strict financial logic and risk management rules.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.models.enums import SignalAction

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None
    risk_reward_ratio: Optional[float] = None


class SignalValidator:
    """
    Strict mathematical validation layer for AI signals.
    """

    MIN_RISK_REWARD = 2.0  # Minimum 1:2 Risk/Reward ratio

    @staticmethod
    def validate(signal_data: Dict[str, Any]) -> ValidationResult:
        try:
            # 1. Extract and cast data safely
            action = signal_data.get("action", "").upper()
            entry = float(signal_data.get("entry_price", 0))
            target = float(signal_data.get("target_price", 0))
            stop = float(signal_data.get("stop_loss", 0))

            # 2. Sanity Checks (No zero/negative prices)
            if entry <= 0 or target <= 0 or stop <= 0:
                return ValidationResult(False, "Prices must be positive")

            if entry == target or entry == stop:
                return ValidationResult(False, "Entry cannot equal Target or Stop")

            # 3. Directional Logic & PnL Calculation
            potential_profit = 0.0
            potential_loss = 0.0

            if action == SignalAction.BUY:
                if target <= entry:
                    return ValidationResult(False, "Buy Logic Error: Target must be > Entry")
                if stop >= entry:
                    return ValidationResult(False, "Buy Logic Error: Stop Loss must be < Entry")

                potential_profit = target - entry
                potential_loss = entry - stop

            elif action == SignalAction.SELL:
                if target >= entry:
                    return ValidationResult(False, "Sell Logic Error: Target must be < Entry")
                if stop <= entry:
                    return ValidationResult(False, "Sell Logic Error: Stop Loss must be > Entry")

                potential_profit = entry - target
                potential_loss = stop - entry

            else:
                return ValidationResult(False, f"Invalid Action: {action}")

            # 4. Risk/Reward Calculation
            if potential_loss == 0:
                return ValidationResult(False, "Invalid Stop Loss (Zero Risk)")

            rr_ratio = round(potential_profit / potential_loss, 2)

            # 5. The "Golden Rule" Check
            if rr_ratio < SignalValidator.MIN_RISK_REWARD:
                return ValidationResult(
                    False,
                    f"Risk/Reward too low (1:{rr_ratio}). Minimum required is 1:{SignalValidator.MIN_RISK_REWARD}",
                )

            return ValidationResult(True, risk_reward_ratio=rr_ratio)

        except ValueError:
            return ValidationResult(False, "Invalid price format (not a number)")
        except Exception as e:
            logger.error("validation_exception", error=str(e))
            return ValidationResult(False, f"Validation System Error: {str(e)}")


signal_validator = SignalValidator()
