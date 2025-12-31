"""
AI Agent for stock analysis.

Uses Google Gemini with 'Triple Confirmation' logic to ensure
only high-quality, catalyst-driven setup are generated.
"""

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import google.genai as genai

from app.core.logging import get_logger
from app.scanner.signal_validator import signal_validator

logger = get_logger(__name__)
client = genai.Client()


def parse_expiration(horizon_str: str) -> datetime:
    """Parses '3-5 Days' into a concrete datetime for the database."""
    try:
        # Default to 5 days if parsing fails
        days = 5
        numbers = [int(n) for n in re.findall(r"\d+", horizon_str)]
        if numbers:
            days = max(numbers)

        if "week" in horizon_str.lower():
            days = days * 7
        elif "month" in horizon_str.lower():
            days = days * 30

        # Hard cap at 45 days for swing trades
        days = min(days, 45)

        return datetime.now(timezone.utc) + timedelta(days=days)
    except Exception:
        return datetime.now(timezone.utc) + timedelta(days=5)


def analyze_opportunity(ticker: str, market_data: Dict[str, Any], news_context: str) -> Optional[Dict[str, Any]]:
    """
    Analyzes stock data using the 'Triple Confirmation' framework.
    Returns a validated signal or None.
    """

    # Strict prompt engineering
    prompt = f"""
    ROLE: You are a Senior Hedge Fund Portfolio Manager (Risk-Averse).
    
    INPUT DATA:
    Stock: {ticker}
    Market Data: {json.dumps(market_data)}
    News Context: 
    {news_context}

    STRICT "TRIPLE CONFIRMATION" CHECKLIST:
    1. TECHNICAL: Is the Trend clearly favourable? (Avoid if RSI > 70 for Buy).
    2. FUNDAMENTAL: Is the company solvent? (Reject if bankruptcy news exists).
    3. CATALYST: Is there a SPECIFIC hard news reason to enter? (Earnings, Contracts, Regulatory approvals).
       *REJECT if news is just "generic market noise" or opinion.*

    TASK:
    - If ANY of the 3 checks fail, return null.
    - If ALL 3 pass, generate a Swing Trade Plan.

    OUTPUT FORMAT (JSON Only):
    {{
        "action": "BUY" | "SELL",
        "confidence_score": 80-100,
        "setup_type": "BREAKOUT" | "PULLBACK" | "REVERSAL" | "MOMENTUM" | "VALUE",
        "reasoning": "Technical: [Trend]. Catalyst: [Specific News].",
        "time_horizon": "e.g. 3-5 Days",
        "entry_price": {market_data.get('current_price')},
        "target_price": <Calculated 6-10% profit>,
        "stop_loss": <Calculated 2-3% risk>
    }}
    """

    try:
        # Using the latest flash model for speed and reasoning
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()

        # 1. Handle Rejection (AI decided it's a bad trade)
        if not text or text == "null":
            logger.info("ai_rejected_trade", ticker=ticker, reason="Triple Confirmation Failed")
            return None

        result = json.loads(text)

        # 2. VALIDATION LAYER (The Math Police)
        validation = signal_validator.validate(result)

        if not validation.is_valid:
            logger.warning("signal_validation_failed", ticker=ticker, error=validation.error, raw_ai_output=result)
            return None

        # 3. Enrich Data for Database
        result["risk_reward"] = validation.risk_reward_ratio

        # Parse text duration to datetime
        raw_horizon = result.get("time_horizon", "5 Days")
        result["time_horizon"] = raw_horizon
        result["expires_at"] = parse_expiration(raw_horizon)

        # Determine Status (Active vs Pending)
        # If entry is > 0.5% away from current price, it's a PENDING order
        current_price = market_data.get("current_price", 0)
        entry_price = float(result.get("entry_price", 0))

        if abs((entry_price - current_price) / current_price) > 0.005:
            result["status"] = "PENDING"
        else:
            result["status"] = "ACTIVE"

        logger.info("ai_analysis_success", ticker=ticker, action=result["action"])
        return result

    except Exception as e:
        logger.error("ai_analysis_error", ticker=ticker, error=str(e))
        return None
