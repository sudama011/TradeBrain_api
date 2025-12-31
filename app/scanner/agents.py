"""
AI Agent for stock analysis.

Uses Google Gemini to analyze market data and news context
to generate trading signals.
"""

import json
from typing import Any, Dict, Optional

import google.genai as genai

from app.core.logging import get_logger

logger = get_logger(__name__)

client = genai.Client()


def analyze_opportunity(ticker: str, market_data: Dict[str, Any], news_context: str) -> Optional[Dict[str, Any]]:
    """
    Sends data to Gemini and returns a JSON decision.

    Args:
        ticker: Stock ticker symbol
        market_data: Dictionary with price data
        news_context: News context string

    Returns:
        Dictionary with action, confidence_score, reasoning, etc.
        or None if analysis failed.
    """
    prompt = f"""
    ROLE: You are a strict, cynical financial analyst. You only care about FACTS.

    TASK: Analyze the following stock data and news.

    STOCK: {ticker}
    PRICE DATA: {market_data}
    NEWS CONTEXT:
    {news_context}

    INSTRUCTIONS:
    1. Ignore vague opinion pieces. Look for hard numbers (Earnings, Orders, Tax changes).
    2. Suggest a trade ONLY if confidence is > 75%.
    3. Calculate sensible Stoploss (approx 2-3% below) and Target (approx 5-6% above) based on current price.

    OUTPUT FORMAT (Strict JSON):
    {{
        "action": "BUY" | "SELL" | "HOLD",
        "confidence_score": 0-100,
        "reasoning": "Brief summary of the specific fact causing this move.",
        "entry_price": {market_data['current_price']},
        "target_price": 0.0,
        "stop_loss": 0.0
    }}
    """

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()

        logger.info("ai_analysis_complete", ticker=ticker)
        result = json.loads(text)
        return result

    except Exception as e:
        logger.error("ai_analysis_error", ticker=ticker, error=str(e))
        return None
