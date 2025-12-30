import asyncio
import time
from datetime import datetime, timezone

import schedule

from app.db.database import AsyncSessionLocal
from app.models.signal import Signal
from scanner.agents import analyze_opportunity
from scanner.tools import get_market_data, get_news_context

# The "Watchlist"
WATCHLIST = ["TATASTEEL", "RELIANCE", "INFY", "ZOMATO"]


async def save_signal(ticker, ai_result, url):
    """Saves the signal to the Database asynchronously."""
    async with AsyncSessionLocal() as db:
        try:
            print(f"💾 Saving Signal: {ticker} | {ai_result['action']}")

            new_signal = Signal(
                ticker=ticker,
                action=ai_result["action"],
                confidence=ai_result["confidence_score"],
                entry_price=ai_result["entry_price"],
                target_price=ai_result["target_price"],
                stop_loss=ai_result["stop_loss"],
                reasoning=ai_result["reasoning"],
                source_url=url,
                created_at=datetime.now(timezone.utc),
            )

            db.add(new_signal)
            await db.commit()
        except Exception as e:
            print(f"❌ DB Error: {e}")
            await db.rollback()


async def job():
    print(f"\n--- 🔄 Scan Started: {datetime.now(timezone.utc)} ---")

    for ticker in WATCHLIST:
        print(f"🔎 Checking {ticker}...")

        try:
            # 1. Fetch Data
            m_data = get_market_data(ticker)
            if not m_data:
                continue

            # 2. Fetch News
            news_text, top_url = get_news_context(ticker)

            # 3. Analyze
            decision = analyze_opportunity(ticker, m_data, news_text)

            # 4. Save if Good
            if decision and decision.get("confidence_score", 0) >= 75:
                await save_signal(ticker, decision, top_url)
            else:
                print(f"   Skipping: Low confidence ({decision.get('confidence_score', 0)}%)")

        except Exception as e:
            print(f"   Error processing {ticker}: {e}")

    print("--- ✅ Scan Complete ---")


def schedule_job():
    """Run job asynchronously."""
    asyncio.run(job())


# Schedule it
schedule.every(30).minutes.do(schedule_job)

if __name__ == "__main__":
    print("🚀 TradeBrain Scanner Online")
    schedule_job()  # Run once immediately
    while True:
        schedule.run_pending()
        time.sleep(1)
