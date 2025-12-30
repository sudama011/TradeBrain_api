from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import signal

router = APIRouter()


@router.get("/signals")
def get_signals(db: Session = Depends(get_db)):
    """
    Fetches the latest trading signals from the database.
    """
    try:
        # Query the DB: Get all signals, ordered by newest first
        signals = db.query(signal.Signal).order_by(signal.Signal.created_at.desc()).limit(50).all()

        return {"status": "success", "count": len(signals), "data": signals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
