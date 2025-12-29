from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime, timezone
from app.database import Base

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)       # e.g., "TATASTEEL"
    action = Column(String)                   # "BUY", "SELL", "HOLD"
    confidence = Column(Integer)              # 0 to 100
    
    entry_price = Column(Float)
    target_price = Column(Float)
    stop_loss = Column(Float)
    
    reasoning = Column(Text)                  # The AI's explanation
    source_url = Column(String, nullable=True) # Link to news source
    
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
