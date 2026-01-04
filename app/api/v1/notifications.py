from uuid import UUID

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_notifications():
    """Paginated list of user alerts."""
    return {"notifications": []}


@router.patch("/{id}/read")
async def mark_as_read(id: UUID):
    """Mark single notification as read."""
    return {"message": f"Notification {id} read"}


@router.patch("/read-all")
async def mark_all_read():
    """Mark all unread notifications as read."""
    return {"message": "All notifications marked as read"}


@router.get("/unread-count")
async def get_unread_count():
    """Count for UI badge."""
    return {"unread_count": 0}
