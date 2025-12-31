"""
Data fetching tools for the scanner.

Provides market data and news context for stock analysis.
"""

import os
from typing import Dict, Optional, Tuple

import yfinance as yf
from dotenv import load_dotenv
from tavily import TavilyClient

from app.core.logging import get_logger

load_dotenv()

logger = get_logger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None


def get_market_data(ticker: str) -> Optional[Dict]:
    """
    Fetches the last 5 days of price data to determine trend.

    Args:
        ticker: Stock ticker symbol (e.g., 'TATASTEEL')

    Returns:
        Dictionary with current_price, change_pct, trend, volume_avg
        or None if data couldn't be fetched.
    """
    try:
        # Append .NS for NSE stocks if not present
        symbol = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
        stock = yf.Ticker(symbol)

        # Get 5 days history
        hist = stock.history(period="5d")

        if hist.empty:
            logger.warning("empty_market_data", ticker=ticker)
            return None

        current_price = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        change_pct = ((current_price - prev_close) / prev_close) * 100

        return {
            "current_price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "trend": "UP" if change_pct > 0 else "DOWN",
            "volume_avg": int(hist["Volume"].mean()),
        }
    except Exception as e:
        logger.error("market_data_fetch_error", ticker=ticker, error=str(e))
        return None


def get_news_context(ticker: str) -> Tuple[str, str]:
    """
    Searches for factual financial news using Tavily.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Tuple of (news_context, top_url)
    """
    if not tavily:
        logger.warning("tavily_not_configured")
        return "", ""

    query = f"{ticker} share news factual financial results sebi circular rbi announcements"
    try:
        response = tavily.search(query=query, search_depth="advanced", max_results=3)

        context = ""
        top_url = ""

        if response.get("results"):
            top_url = response["results"][0]["url"]
            for result in response["results"]:
                context += f"- {result['content']} (Source: {result['url']})\n"

        return context, top_url
    except Exception as e:
        logger.error("news_fetch_error", ticker=ticker, error=str(e))
        return "", ""


def check_api_health() -> Dict:
    """
    Check health status of external APIs.

    Returns:
        Dictionary with API health status
    """
    health = {
        "tavily": {"configured": bool(TAVILY_API_KEY), "status": "unknown"},
        "yfinance": {"status": "unknown"},
    }

    # Check Tavily
    if tavily:
        try:
            # Simple test query
            tavily.search(query="test", max_results=1)
            health["tavily"]["status"] = "healthy"
        except Exception as e:
            health["tavily"]["status"] = f"error: {str(e)[:50]}"
    else:
        health["tavily"]["status"] = "not_configured"

    # Check yfinance
    try:
        test_stock = yf.Ticker("RELIANCE.NS")
        hist = test_stock.history(period="1d")
        health["yfinance"]["status"] = "healthy" if not hist.empty else "no_data"
    except Exception as e:
        health["yfinance"]["status"] = f"error: {str(e)[:50]}"

    return health
