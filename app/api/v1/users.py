from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_my_profile():
    """Retrieve current user profile."""
    return {"email": "user@example.com", "full_name": "Placeholder User"}


@router.patch("/me")
async def update_profile():
    """Update profile details."""
    return {"message": "Profile updated"}


@router.post("/devices")
async def register_device():
    """Register FCM/APNS token."""
    return {"message": "Device registered"}


@router.delete("/devices/{token}")
async def unregister_device(token: str):
    """Unregister a specific device token."""
    return {"message": f"Device {token} removed"}
