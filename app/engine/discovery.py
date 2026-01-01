"""
Discovery Engine.

Scans generic market news to identify 'Stocks in Play' (Catalysts)
and extracts ticker symbols to feed into the main scanner.
"""

import json
import re
from typing import List

import google.genai as genai
from tavily import TavilyClient

from app.core.logger import get_logger
from app.engine.market_data import TAVILY_API_KEY

logger = get_logger(__name__)

# Initialize Clients
tavily = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
client = genai.Client()


def get_trending_tickers() -> List[str]:
    """
    1. Searches news for 'Indian Stock Market Breaking News'.
    2. Uses Gemini to extract specific Tickers (e.g., 'INFY', 'TATAMOTORS').
    3. Returns a distinct list of valid NSE tickers.
    """
    if not tavily:
        logger.warning("discovery_skipped_no_tavily")
        return []

    logger.info("discovery_scan_started")

    # 1. Broad Search for Catalysts
    # We search for specific keywords that imply volatility/opportunity
    queries = [
        "NSE India stock market breaking news today earnings",
        "Indian companies winning big contracts today",
        "Stocks hitting 52 week high with high volume NSE India",
        "RBI announcements impact on specific stocks today",
    ]

    combined_news = ""

    try:
        for q in queries:
            response = tavily.search(query=q, search_depth="basic", max_results=3)
            if response.get("results"):
                for r in response["results"]:
                    combined_news += f"- {r['content']}\n"
    except Exception as e:
        logger.error("discovery_search_failed", error=str(e))
        return []

    if not combined_news:
        return []

    # 2. Extract Tickers using AI
    prompt = f"""
    ROLE: Financial Data Extractor.
    TASK: Identify Indian NSE Stock Tickers mentioned in the text below.
    
    INPUT TEXT:
    {combined_news[:5000]} # Truncate to avoid token limits

    RULES:
    1. Extract ONLY standard NSE Ticker symbols (e.g. RELIANCE, TCS, INFY).
    2. Ignore indices (NIFTY, SENSEX).
    3. Return a raw JSON list of strings.
    4. If no tickers found, return [].

    OUTPUT FORMAT: ["TICKER1", "TICKER2"]
    """

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text.strip()
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if not json_match:
            return []

        tickers: List[str] = json.loads(json_match.group())

        # 3. Clean and Validate
        cleaned_tickers = []
        for t in tickers:
            t = t.upper().replace(".NS", "").strip()
            # Basic validation: 3-20 chars, alphanumeric
            if t.isalnum() and 3 <= len(t) <= 20:
                cleaned_tickers.append(t)

        # Deduplicate
        final_list = list(set(cleaned_tickers))
        logger.info("discovery_success", tickers_found=len(final_list), tickers=final_list)

        return final_list

    except Exception as e:
        logger.error("discovery_extraction_failed", error=str(e))
        return []
