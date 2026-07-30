"""Integration tests for notification event coverage + idempotency (doc §16)."""
import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import Auction, AuctionStatus, Category, Notification, NotificationType, User
from app.core.security import create_access_token
from app.services.notifications import send_notification


class TestSendNotificationIdempotency:
    async def test_duplicate_event_key_is_skipped(self, db_session: AsyncSession, test_user: User):
        """Doc §16.2: retried events (same event_key) must not create a second row or email."""
        key = f"test_event:{uuid.uuid4()}"
        first = await send_notification(
            db_session, test_user.id, NotificationType.auction_joined,
            "Title", "Message", send_email=False, event_key=key,
        )
        assert first is not None

        second = await send_notification(
            db_session, test_user.id, NotificationType.auction_joined,
            "Title", "Message", send_email=False, event_key=key,
        )
        assert second is None

        result = await db_session.execute(
            select(Notification).where(Notification.event_key == key)
        )
        assert len(result.scalars().all()) == 1

    async def test_no_event_key_allows_multiple_rows(self, db_session: AsyncSession, test_user: User):
        """Notifications without an event_key (one-off, non-retried actions) are unaffected."""
        await send_notification(
            db_session, test_user.id, NotificationType.bid_received, "A", "A", send_email=False,
        )
        await send_notification(
            db_session, test_user.id, NotificationType.bid_received, "B", "B", send_email=False,
        )
        result = await db_session.execute(
            select(Notification).where(Notification.user_id == test_user.id)
        )
        assert len(result.scalars().all()) == 2


class TestPreferredLanguageEmail:
    """Doc §16.3: the email body must follow User.preferred_language; the in-app
    notification row always stays English regardless."""

    async def test_me_preference_uses_montenegrin_email_body(
        self, db_session: AsyncSession, test_user: User, monkeypatch,
    ):
        import app.services.notifications as notif_module
        test_user.preferred_language = "me"
        await db_session.commit()

        sent = {}
        def fake_send_email(to, subject, body):
            sent["subject"] = subject
            sent["body"] = body
        monkeypatch.setattr(notif_module, "_send_email", fake_send_email)

        await send_notification(
            db_session, test_user.id, NotificationType.bid_received,
            "New bid", "English body", send_email=True,
            title_me="Nova ponuda", message_me="Crnogorski tekst",
        )
        assert sent["subject"] == "Nova ponuda"
        assert sent["body"] == "Crnogorski tekst"

        # In-app row is unaffected - still stores the English strings the caller passed.
        result = await db_session.execute(
            select(Notification).where(Notification.user_id == test_user.id, Notification.type == NotificationType.bid_received)
        )
        row = result.scalars().first()
        assert row.title == "New bid" and row.message == "English body"

    async def test_no_preference_falls_back_to_english_email_body(
        self, db_session: AsyncSession, test_user: User, monkeypatch,
    ):
        import app.services.notifications as notif_module
        assert test_user.preferred_language is None

        sent = {}
        def fake_send_email(to, subject, body):
            sent["subject"] = subject
            sent["body"] = body
        monkeypatch.setattr(notif_module, "_send_email", fake_send_email)

        await send_notification(
            db_session, test_user.id, NotificationType.outbid,
            "Outbid", "English body", send_email=True,
            title_me="Nadmašeni", message_me="Crnogorski tekst",
        )
        assert sent["subject"] == "Outbid"
        assert sent["body"] == "English body"


class TestJoinAuctionNotification:
    async def test_join_fires_notification_once(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category,
    ):
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Joinable Auction",
            description="desc",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AuctionStatus.live,
        )
        db_session.add(auction)
        await db_session.commit()

        buyer = User(
            id=str(uuid.uuid4()),
            name="Joiner",
            email=f"joiner_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role="buyer",
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
            credits_balance=100.0,
        )
        db_session.add(buyer)
        await db_session.commit()
        buyer_headers = {"Authorization": f"Bearer {create_access_token(data={'sub': buyer.id, 'role': 'buyer'})}"}

        r1 = await async_client.post(f"/api/auctions/{auction.id}/join", headers=buyer_headers)
        assert r1.status_code == 200
        r2 = await async_client.post(f"/api/auctions/{auction.id}/join", headers=buyer_headers)
        assert r2.status_code == 200
        assert r2.json()["already_joined"] is True

        result = await db_session.execute(
            select(Notification).where(
                Notification.user_id == buyer.id,
                Notification.type == NotificationType.auction_joined,
            )
        )
        assert len(result.scalars().all()) == 1
