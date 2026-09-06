"""Isolated performance probe. Run from repository root; never uses deployed DB/SMTP."""
import asyncio
import gzip
import json
import logging
import os
from pathlib import Path
import statistics
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.update(DATABASE_URL="sqlite+aiosqlite://", JWT_SECRET="isolated-performance-probe",
                  ENVIRONMENT="development", SMTP_HOST="", SMTP_USER="", SMTP_PASSWORD="")

import httpx
from sqlalchemy import event, insert, text
from app.core.database import engine, Base, AsyncSessionLocal, get_db
from app.core.security import create_access_token
from app.models.domain import User, Category, Auction, Bid, AuctionImage, AuctionParticipant, _utcnow
from app.api.ws import ConnectionManager
from app.services.notifications import deliver_pending_emails
from main import app
from datetime import timedelta

logging.disable(logging.CRITICAL)
app.state.limiter.enabled = False
queries = []


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def count_query(conn, cursor, statement, parameters, context, executemany):
    queries.append(statement)


async def isolated_db():
    async with AsyncSessionLocal() as session:
        yield session


async def main():
    now = _utcnow()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(insert(User), [dict(id=u, name=u, email=u+"@example.invalid",
            password_hash="not-a-login-hash", role=role, email_verified=True)
            for u, role in [("seller", "seller"), ("buyer", "buyer"), ("admin", "admin")]])
        await conn.execute(insert(Category), [dict(id=1, name="Vehicles", slug="vehicles")])
        await conn.execute(insert(Auction), [dict(id=f"a{i}", seller_id="seller", category_id=1,
            title=f"Auction {i}", description="Test description " * 20, start_price=1,
            current_price=100, min_increment=1, status="live", start_time=now-timedelta(days=1),
            end_time=now+timedelta(hours=2), created_at=now) for i in range(1000)])
        for start in range(0, 100000, 10000):
            await conn.execute(insert(Bid), [dict(id=f"b{i}", auction_id=f"a{i//100}",
                user_id="buyer", amount=i % 100 + 1, created_at=now, invalidated=False)
                for i in range(start, start+10000)])
        await conn.execute(insert(AuctionImage), [dict(id=f"im{i}", auction_id=f"a{i//5}",
            image_url="/uploads/synthetic.webp") for i in range(5000)])
        await conn.execute(insert(AuctionParticipant), [dict(id="seller-join", auction_id="a0",
            user_id="admin", credits_spent=0)])

    app.dependency_overrides[get_db] = isolated_db
    headers = {u: {"Authorization": "Bearer " + create_access_token({"sub": u, "role": role})}
               for u, role in [("buyer", "buyer"), ("admin", "admin")]}
    results = {"environment": sys.version, "dataset": {"auctions": 1000, "bids": 100000, "images": 5000},
               "method": "In-process HTTP ASGI; in-memory SQLite; one warmup then five sequential requests; real JWT validation; no lifespan/scheduler/proxy/network."}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://probe") as client:
        async def measure(path, user=None):
            samples = []
            for i in range(6):
                queries.clear()
                start = time.perf_counter()
                response = await client.get(path, headers=headers.get(user, {}))
                elapsed = (time.perf_counter()-start)*1000
                assert response.status_code == 200, (path, response.status_code, response.text[:200])
                if i:
                    samples.append(elapsed)
            return {"median_ms": round(statistics.median(samples), 2), "range_ms": [round(min(samples), 2), round(max(samples), 2)],
                    "sql_queries": len(queries), "response_bytes": len(response.content)}

        results["list_24"] = await measure("/api/auctions?limit=24")
        results["bid_history_50"] = await measure("/api/auctions/a0/bids")
        results["admin_page_50"] = await measure("/api/admin/auctions?limit=50", "admin")
        for count, previous in [(1, 0), (10, 1), (100, 10)]:
            async with engine.begin() as conn:
                await conn.execute(insert(AuctionParticipant), [dict(id=f"p{i}", auction_id=f"a{i}",
                    user_id="buyer", credits_spent=0) for i in range(previous, count)])
            results[f"joined_{count}"] = await measure("/api/auctions/joined?limit=100", "buyer")

        email_calls = []
        def fake_email(*args):
            email_calls.append(time.perf_counter())
            time.sleep(0.1)
            return True
        with patch("app.services.notifications._send_email", fake_email), patch("app.services.notifications._get_smtp_config", return_value={"configured": True}):
            start = time.perf_counter()
            response = await client.post("/api/auctions/a0/bids", headers=headers["admin"], json={"amount": 101})
            elapsed = (time.perf_counter()-start)*1000
            assert email_calls == [], "SMTP ran inside the request"
            await deliver_pending_emails()
        assert response.status_code == 201, response.text
        assert len(email_calls) == 2
        results["bid_with_two_simulated_100ms_emails"] = {"request_ms": round(elapsed, 2), "inline_email_calls": 0, "worker_email_calls": len(email_calls)}
        for path in ["/", "/assets/js/api.js"]:
            response = await client.get(path, headers={"Accept-Encoding": "gzip, br"})
            assert response.status_code == 200
            results[f"headers_{path}"] = {key: response.headers.get(key) for key in ["content-encoding", "cache-control", "etag"]}

    sql = "SELECT id, user_id, amount FROM bids WHERE auction_id = 'a0' AND invalidated = 0 ORDER BY amount DESC, created_at ASC LIMIT 1"
    async with engine.begin() as conn:
        await conn.execute(text("DROP INDEX ix_bids_auction_ranking"))
        for label in ["before", "after"]:
            if label == "after":
                await conn.execute(text("CREATE INDEX probe_bid_lookup ON bids (auction_id, invalidated, amount DESC, created_at ASC)"))
            plan = (await conn.execute(text("EXPLAIN QUERY PLAN " + sql))).all()
            times = []
            for i in range(21):
                start = time.perf_counter()
                row = (await conn.execute(text(sql))).first()
                assert row
                if i:
                    times.append((time.perf_counter()-start)*1000)
            results[f"bid_index_{label}"] = {"median_ms": round(statistics.median(times), 3), "plan": [list(r) for r in plan]}

    class SlowSocket:
        async def send_text(self, payload):
            await asyncio.sleep(0.01)
    manager = ConnectionManager()
    manager.active_connections["probe"] = {"connections": {SlowSocket() for _ in range(20)}}
    start = time.perf_counter()
    await manager.broadcast("probe", {"type": "probe"})
    results["broadcast_20_simulated_10ms_sockets"] = {"total_ms": round((time.perf_counter()-start)*1000, 2)}
    files = ["index.html", "assets/css/style.css", "assets/js/main.js", "assets/js/i18n.js", "assets/js/api.js"]
    results["initial_text"] = {"raw_bytes": sum((ROOT/f).stat().st_size for f in files),
        "gzip_bytes": sum(len(gzip.compress((ROOT/f).read_bytes())) for f in files)}
    app.dependency_overrides.clear()
    await engine.dispose()
    output = json.dumps(results, indent=2)
    Path(__file__).with_name("after-results.json").write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    asyncio.run(main())
