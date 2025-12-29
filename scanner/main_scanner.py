import time
import schedule
from datetime import datetime
from app.database import SessionLocal
from app.models import Signal
from scanner.tools import get_market_data, get_news_context
from scanner.agents import analyze_opportunity

# The "Watchlist"
WATCHLIST = ["TATASTEEL", "RELIANCE", "INFY", "ZOMATO"]

def save_signal(ticker, ai_result, url):
    """Saves the signal to the Database"""
    db = SessionLocal()
    try:
        print(f"💾 Saving Signal: {ticker} | {ai_result['action']}")
        
        new_signal = Signal(
            ticker=ticker,
            action=ai_result['action'],
            confidence=ai_result['confidence_score'],
            entry_price=ai_result['entry_price'],
            target_price=ai_result['target_price'],
            stop_loss=ai_result['stop_loss'],
            reasoning=ai_result['reasoning'],
            source_url=url,
            created_at=datetime.now()
        )
        
        db.add(new_signal)
        db.commit()
    except Exception as e:
        print(f"❌ DB Error: {e}")
    finally:
        db.close()

def job():
    print(f"\n--- 🔄 Scan Started: {datetime.now()} ---")
    
    for ticker in WATCHLIST:
        print(f"🔎 Checking {ticker}...")
        
        # 1. Fetch Data
        m_data = get_market_data(ticker)
        if not m_data: continue
        
        # 2. Fetch News
        news_text, top_url = get_news_context(ticker)
        
        # 3. Analyze
        decision = analyze_opportunity(ticker, m_data, news_text)
        
        # 4. Save if Good
        if decision and decision['confidence_score'] >= 75:
            save_signal(ticker, decision, top_url)
        else:
            print(f"   Skipping: Low confidence ({decision.get('confidence_score', 0)}%)")
            
    print("--- ✅ Scan Complete ---")

# Schedule it
schedule.every(30).minutes.do(job)

if __name__ == "__main__":
    print("🚀 TradeBrain Scanner Online")
    job() # Run once immediately
    while True:
        schedule.run_pending()
        time.sleep(1)