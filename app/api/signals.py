from fastapi import APIRouter

router = APIRouter()

@router.get("/signals")
def get_signals():
    return {"status": "No signals yet", "data": []}