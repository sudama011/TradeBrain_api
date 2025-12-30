import os

import yfinance as yf
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=TAVILY_API_KEY)


def get_market_data(ticker):
    """
    Fetches the last 5 days of price data to determine trend.
    """
    try:
        # Append .NS for NSE stocks if not present
        symbol = ticker if ticker.endswith(".NS") else f"{ticker}.NS"
        stock = yf.Ticker(symbol)

        # Get 5 days history
        hist = stock.history(period="5d")

        if hist.empty:
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
        print(f"❌ Error fetching price for {ticker}: {e}")
        return None


def get_news_context(ticker):
    """
    Searches for factual financial news using Tavily.
    """
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
        print(f"❌ Error fetching news for {ticker}: {e}")
        return "", ""
