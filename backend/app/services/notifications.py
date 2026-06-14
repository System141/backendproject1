"""Notification service: in-app + email notifications.

Design (ponytail: minimal path):
- In-app notifications are always saved to DB.
- Email sending is async via stdlib smtplib (no extra dep).
- Email config via env vars; if not configured, email is silently skipped.
"""
import os
import smtplib
import uuid
from email.message import EmailMessage
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import Notification, NotificationType, User, Auction


def _get_smtp_config() -> Optional[dict]:
    """Return SMTP config dict or None if not configured."""
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT", "587")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("SMTP_FROM", "noreply@bidmont.com")
    if not host or not user or not password:
        return None
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "from_addr": from_addr,
    }


def _send_email(to: str, subject: str, body: str):
    """Send an email via SMTP. Silently ignores if SMTP not configured."""
    config = _get_smtp_config()
    if not config:
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = config["from_addr"]
    msg["To"] = to

    try:
        with smtplib.SMTP(config["host"], config["port"]) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.send_message(msg)
    except Exception:
        pass  # ponytail: silently fail — don't break the app for email


async def send_notification(
    db: AsyncSession,
    user_id: str,
    notification_type: NotificationType,
    title: str,
    message: str,
    auction_id: Optional[str] = None,
    send_email: bool = True,
):
    """Create an in-app notification and optionally send an email."""
    # Save to DB
    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        auction_id=auction_id,
        is_read=False,
    )
    db.add(notif)
    await db.commit()

    # Send email if configured and requested
    if send_email:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user and user.email:
            _send_email(user.email, title, message)

    return notif