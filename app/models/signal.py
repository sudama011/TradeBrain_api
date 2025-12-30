from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.core.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)  # e.g., "TATASTEEL"
    action = Column(String, nullable=False)  # "BUY", "SELL", "HOLD"
    confidence = Column(Integer, nullable=False)  # 0 to 100

    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)

    reasoning = Column(Text, nullable=False)  # The AI's explanation
    source_url = Column(String, nullable=True)  # Link to news source

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
