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

from app.models.domain import Notification, NotificationType, NotificationTemplate, User, Auction, UserRole

# Doc §17 admin panel checklist: "Notification template management". Only
# these types can be admin-customized - each entry lists the placeholder
# names its call site actually passes via template_vars. Wiring more types
# just means adding them here + passing template_vars at that call site;
# every other type is untouched (send_notification() ignores templates when
# template_vars is None, which is the default for every unwired call site).
TEMPLATABLE_NOTIFICATION_TYPES: dict[NotificationType, list[str]] = {
    NotificationType.auction_approved: ["auction_title"],
    NotificationType.auction_rejected: ["auction_title"],
    NotificationType.listing_changes_requested: ["auction_title", "reason"],
    NotificationType.credit_purchase_successful: ["credits_amount"],
    NotificationType.credit_purchase_failed: ["credits_amount"],
}


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


def _render_template_field(template_value: Optional[str], template_vars: dict, fallback: str) -> str:
    """Use the admin's saved template text only if it's set AND every
    placeholder it references is present in template_vars - a typo'd or
    stale placeholder (e.g. after a call site's vars change) falls back to
    today's literal string rather than raising or rendering '{oops}' to a
    real user."""
    if not template_value:
        return fallback
    try:
        return template_value.format(**template_vars)
    except (KeyError, IndexError):
        return fallback


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
    template_vars: Optional[dict] = None,
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

    template_vars (doc §17 admin panel: "Notification template management"):
    pass a dict of the dynamic values this call site's title/message/
    title_me/message_me were built from (see TEMPLATABLE_NOTIFICATION_TYPES
    for which types + which var names). If an admin has saved a custom
    template for this notification_type, its text is used instead - but only
    per-field, and only when that field's placeholders all resolve from
    template_vars. This can never silently drop a caller's dynamic content:
    a field with no saved override, or one whose placeholders don't match,
    just keeps the literal value the caller already passed.
    """
    if template_vars is not None:
        result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.type == notification_type.value))
        template = result.scalars().first()
        if template:
            title = _render_template_field(template.title_en, template_vars, title)
            message = _render_template_field(template.message_en, template_vars, message)
            title_me = _render_template_field(template.title_me, template_vars, title_me) if title_me else title_me
            message_me = _render_template_field(template.message_me, template_vars, message_me) if message_me else message_me

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


async def alert_admins(db: AsyncSession, title: str, message: str, event_key: Optional[str] = None):
    """Doc §19.7: 'kritik hata icin admin teknik ekibe uyari uretmeli' - route
    a system-level failure (bid engine, payment webhook, unhandled 500) to
    every admin/super_admin as an in-app + email notification, reusing the
    existing notification infra rather than standing up a separate paging
    service. event_key dedupes repeated identical alerts the same way normal
    notifications do (e.g. a scheduler loop hitting the same error every 30s).

    Real external paging (Slack/PagerDuty/uptime monitor) is a LITZOR
    operational choice (doc §19.1 makes the same call for domain/TLS) - this
    is the code-completable half: the alert always lands somewhere a human
    checks (admin notification bell + email) even before that choice is made.

    Notification.event_key is unique *globally*, not per-user - passing the
    same event_key for every admin in the loop below would let only the
    first admin's insert claim it and silently drop the rest as "duplicates".
    Each admin gets their own key (event_key suffixed with their id) so the
    same underlying incident dedupes per-admin without dropping other admins."""
    result = await db.execute(select(User.id).where(User.role.in_([UserRole.admin, UserRole.super_admin])))
    admin_ids = result.scalars().all()
    for admin_id in admin_ids:
        await send_notification(
            db, admin_id, NotificationType.system_alert, title, message,
            send_email=True, event_key=f"{event_key}:{admin_id}" if event_key else None,
        )