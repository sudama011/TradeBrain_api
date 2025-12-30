from sqlalchemy import Column, Float, Integer, String, Text

from app.models.base_models import BaseModel


class Signal(BaseModel):
    __tablename__ = "signals"

    ticker = Column(String, index=True, nullable=False)  # e.g., "TATASTEEL"
    action = Column(String, nullable=False)  # "BUY", "SELL", "HOLD"
    confidence = Column(Integer, nullable=False)  # 0 to 100

    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)

    reasoning = Column(Text, nullable=False)  # The AI's explanation
    source_url = Column(String, nullable=True)  # Link to news source
