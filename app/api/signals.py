from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter()

@router.get("/signals")
def get_signals(db: Session = Depends(get_db)):
    """
    Fetches the latest trading signals from the database.
    """
    try:
        # Query the DB: Get all signals, ordered by newest first
        signals = db.query(models.Signal)\
            .order_by(models.Signal.created_at.desc())\
            .limit(50)\
            .all()
        
        return {
            "status": "success",
            "count": len(signals),
            "data": signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")