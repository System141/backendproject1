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
from sqlalchemy.exc import IntegrityError

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
    event_key: Optional[str] = None,
    title_me: Optional[str] = None,
    message_me: Optional[str] = None,
):
    """Create an in-app notification and optionally send an email.

    event_key (doc §16.2): pass a deterministic string identifying this
    exact event (e.g. f"ending_soon:{auction.id}") when the caller might be
    invoked more than once for the same real-world event (scheduler polling,
    a payment gateway retrying its callback). A duplicate event_key is
    treated as "already notified" and silently skipped - no email, no
    second row - rather than raising, so a retried caller never has to
    special-case this.

    title_me/message_me (doc §16.3): Montenegrin translations used only for
    the *email* body, selected when the recipient's User.preferred_language
    is "me". The in-app notification row always stores the (English)
    title/message - the doc only requires the email to match the user's
    language, not the notification-bell text.
    """
    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        auction_id=auction_id,
        is_read=False,
        event_key=event_key,
    )
    if event_key:
        try:
            # SAVEPOINT: see get_or_create_settings for why this isn't a full rollback.
            async with db.begin_nested():
                db.add(notif)
        except IntegrityError:
            return None  # already sent for this event_key
        await db.commit()
    else:
        db.add(notif)
        await db.commit()

    # Send email if configured and requested
    if send_email:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if user and user.email:
            use_me = user.preferred_language == "me" and title_me and message_me
            _send_email(user.email, title_me if use_me else title, message_me if use_me else message)

    return notif