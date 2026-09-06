"""Checks for bounded queries, deferred delivery and media authorization."""
import asyncio
import io
from datetime import timedelta

from PIL import Image
from sqlalchemy import event, insert, select

from app.models.domain import Auction, AuctionImage, AuctionParticipant, Bid, NotificationEmail, NotificationType, _utcnow
from app.services.notifications import send_notification, deliver_pending_emails
from tests.conftest import test_engine, TestSessionLocal


async def test_joined_pagination_and_leaders_use_constant_queries(async_client, db_session, test_user, seller_user, test_category, auth_headers):
    now = _utcnow()
    await db_session.execute(insert(Auction), [dict(id=f"perf-a{i}", seller_id=seller_user.id, category_id=test_category.id,
        title=f"Auction {i}", description="Test", status="live", start_price=1, current_price=2, min_increment=1,
        start_time=now, end_time=now+timedelta(hours=1)) for i in range(101)])
    await db_session.execute(insert(AuctionParticipant), [dict(id=f"perf-p{i:03}", user_id=test_user.id,
        auction_id=f"perf-a{i}", credits_spent=0, joined_at=now) for i in range(101)])
    await db_session.execute(insert(Bid), [
        dict(id="valid", auction_id="perf-a0", user_id=test_user.id, amount=2, invalidated=False, created_at=now),
        dict(id="invalid", auction_id="perf-a0", user_id=seller_user.id, amount=5, invalidated=True, created_at=now),
        dict(id="early", auction_id="perf-a1", user_id=seller_user.id, amount=2, invalidated=False, created_at=now-timedelta(seconds=1)),
        dict(id="late", auction_id="perf-a1", user_id=test_user.id, amount=2, invalidated=False, created_at=now),
    ])
    await db_session.commit()
    statements = []
    def count(*args):
        statements.append(args[2])
    event.listen(test_engine.sync_engine, "before_cursor_execute", count)
    try:
        response = await async_client.get("/api/auctions/joined?limit=100", headers=auth_headers)
    finally:
        event.remove(test_engine.sync_engine, "before_cursor_execute", count)
    assert response.status_code == 200
    assert len(statements) == 3  # authentication, count, one indexed page query
    assert response.headers["X-Total-Count"] == "101"
    rows = response.json()
    assert len(rows) == 100
    assert [r["my_bid_status"] for r in rows[:3]] == ["highest", "outbid", "no_bid"]
    last = await async_client.get("/api/auctions/joined?limit=100&offset=100", headers=auth_headers)
    assert len(last.json()) == 1 and last.json()[0]["auction_id"] not in {r["auction_id"] for r in rows}
    public = await async_client.get("/api/auctions?limit=24&offset=96")
    assert len(public.json()) == 5


async def test_email_outbox_dedupes_retries_and_does_not_send_inline(db_session, test_user, monkeypatch):
    import app.services.notifications as notifications
    monkeypatch.setattr(notifications, "_get_smtp_config", lambda: {"configured": True})
    calls = []
    def deliver(*args):
        calls.append(args)
        if len(calls) == 1:
            raise RuntimeError("simulated SMTP failure")
        return True
    monkeypatch.setattr(notifications, "_send_email", deliver)
    for _ in range(2):
        await send_notification(db_session, test_user.id, NotificationType.outbid, "Title", "Body", event_key="outbox-test")
    assert calls == []
    await deliver_pending_emails(TestSessionLocal)
    async with TestSessionLocal() as db:
        rows = (await db.execute(select(NotificationEmail))).scalars().all()
        assert len(rows) == 1 and rows[0].attempts == 1 and rows[0].sent_at is None
        rows[0].next_attempt_at = _utcnow() - timedelta(seconds=1)
        await db.commit()
    await deliver_pending_emails(TestSessionLocal)
    await deliver_pending_emails(TestSessionLocal)
    assert len(calls) == 2
    async with TestSessionLocal() as db:
        row = await db.get(NotificationEmail, rows[0].notification_id)
        assert row.attempts == 2 and row.sent_at is not None


async def test_thumbnail_is_small_cached_and_authorized(async_client, db_session, seller_user, test_category, seller_headers, tmp_path, monkeypatch):
    import app.api.uploads as uploads
    monkeypatch.setattr(uploads, "UPLOAD_DIR", str(tmp_path))
    with Image.new("RGB", (1200, 800), "red") as source:
        source.save(tmp_path / "photo.png")
    now = _utcnow()
    db_session.add(Auction(id="thumb-auction", seller_id=seller_user.id, category_id=test_category.id,
        title="Photo", description="Test", start_price=1, current_price=1, min_increment=1,
        start_time=now, end_time=now+timedelta(hours=1), status="live"))
    db_session.add(AuctionImage(id="thumb-image", auction_id="thumb-auction", image_url="/uploads/photo.png", visibility="private"))
    await db_session.commit()
    url = "/api/uploads/thumb-image/download?thumbnail=true"
    assert (await async_client.get(url)).status_code == 401
    response = await async_client.get(url, headers=seller_headers)
    assert response.status_code == 200 and response.headers["cache-control"] == "private, no-store"
    with Image.open(io.BytesIO(response.content)) as thumbnail:
        assert thumbnail.format == "WEBP" and thumbnail.width <= 320 and thumbnail.height <= 240
    cache = tmp_path / ".thumbnails" / "photo.png.webp"
    modified = cache.stat().st_mtime_ns
    assert (await async_client.get(url, headers=seller_headers)).status_code == 200
    assert cache.stat().st_mtime_ns == modified
    assert (await async_client.get(url)).status_code == 401


async def test_slow_websocket_does_not_hold_fast_clients(monkeypatch):
    import app.api.ws as ws_module
    monkeypatch.setattr(ws_module, "SEND_TIMEOUT_SECONDS", 0.1)
    fast_sent = asyncio.Event()
    class Fast:
        async def send_text(self, payload):
            fast_sent.set()
    class Slow:
        async def send_text(self, payload):
            await asyncio.Event().wait()
    fast, slow = Fast(), Slow()
    manager = ws_module.ConnectionManager()
    manager.active_connections["test"] = {"connections": {slow, fast}}
    pending = asyncio.create_task(manager.broadcast("test", {"type": "test"}))
    await asyncio.wait_for(fast_sent.wait(), 0.08)
    await asyncio.wait_for(pending, 1)
    assert manager.active_connections["test"]["connections"] == {fast}
