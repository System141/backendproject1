from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, update

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import Notification, User
from app.schemas.notification import NotificationResponse

notifications_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@notifications_router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's notifications, newest first."""
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(50)
    )
    notifs = result.scalars().all()
    return [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            type=n.type.value if hasattr(n.type, "value") else str(n.type),
            title=n.title,
            message=n.message,
            auction_id=n.auction_id,
            is_read=n.is_read,
            created_at=str(n.created_at) if n.created_at else "",
        )
        for n in notifs
    ]


@notifications_router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the count of unread notifications."""
    from sqlalchemy import func
    result = await db.execute(
        select(func.count(Notification.id))
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    count = result.scalar()
    return {"count": count}


@notifications_router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.is_read = True
    await db.commit()
    await db.refresh(notif)

    return NotificationResponse(
        id=notif.id,
        user_id=notif.user_id,
        type=notif.type.value if hasattr(notif.type, "value") else str(notif.type),
        title=notif.title,
        message=notif.message,
        auction_id=notif.auction_id,
        is_read=notif.is_read,
        created_at=str(notif.created_at) if notif.created_at else "",
    )