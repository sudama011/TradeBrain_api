from fastapi import APIRouter

router = APIRouter()


@router.get("/logs")
async def get_system_logs():
    """View SystemLog entries for monitoring health."""
    return {"logs": []}


@router.post("/scanner/run")
async def trigger_manual_scan():
    """Manually trigger a background market scan."""
    return {"message": "Manual scan triggered"}
