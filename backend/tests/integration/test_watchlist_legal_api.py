"""Integration tests for the watchlist (doc §10.5) and legal document (doc §15) APIs."""
import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Auction, AuctionStatus, Category, User


async def _make_auction(db_session: AsyncSession, seller: User, category: Category) -> Auction:
    auction = Auction(
        id=str(uuid.uuid4()),
        seller_id=seller.id,
        category_id=category.id,
        title="Watchable Auction",
        description="Track me",
        start_price=100.0,
        current_price=100.0,
        min_increment=10.0,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(days=3),
        status=AuctionStatus.live,
    )
    db_session.add(auction)
    await db_session.commit()
    await db_session.refresh(auction)
    return auction


class TestWatchlist:
    async def test_add_list_remove(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, auth_headers: dict, test_category: Category
    ):
        auction = await _make_auction(db_session, seller_user, test_category)

        add_resp = await async_client.post(f"/api/watchlist/{auction.id}", headers=auth_headers)
        assert add_resp.status_code == 204

        list_resp = await async_client.get("/api/watchlist", headers=auth_headers)
        assert list_resp.status_code == 200
        assert [a["id"] for a in list_resp.json()] == [auction.id]

        remove_resp = await async_client.delete(f"/api/watchlist/{auction.id}", headers=auth_headers)
        assert remove_resp.status_code == 204

        list_resp2 = await async_client.get("/api/watchlist", headers=auth_headers)
        assert list_resp2.json() == []

    async def test_add_idempotent(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, auth_headers: dict, test_category: Category
    ):
        auction = await _make_auction(db_session, seller_user, test_category)

        for _ in range(2):
            resp = await async_client.post(f"/api/watchlist/{auction.id}", headers=auth_headers)
            assert resp.status_code == 204

        list_resp = await async_client.get("/api/watchlist", headers=auth_headers)
        assert len(list_resp.json()) == 1

    async def test_add_nonexistent_auction_404(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.post(f"/api/watchlist/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404


class TestLegalDocuments:
    async def test_no_active_document_404(self, async_client: AsyncClient):
        resp = await async_client.get("/api/legal/terms_of_use")
        assert resp.status_code == 404

    async def test_admin_publish_and_public_fetch(self, async_client: AsyncClient, admin_headers: dict):
        create_resp = await async_client.post(
            "/api/admin/legal",
            json={"document_type": "terms_of_use", "version": "1.0", "content": "Terms v1", "is_active": True},
            headers=admin_headers,
        )
        assert create_resp.status_code == 201

        get_resp = await async_client.get("/api/legal/terms_of_use")
        assert get_resp.status_code == 200
        assert get_resp.json()["version"] == "1.0"

    async def test_duplicate_version_conflict(self, async_client: AsyncClient, admin_headers: dict):
        payload = {"document_type": "cookie_policy", "version": "1.0", "content": "v1", "is_active": True}
        first = await async_client.post("/api/admin/legal", json=payload, headers=admin_headers)
        assert first.status_code == 201

        second = await async_client.post("/api/admin/legal", json=payload, headers=admin_headers)
        assert second.status_code == 409

    async def test_new_version_deactivates_old(self, async_client: AsyncClient, admin_headers: dict):
        await async_client.post(
            "/api/admin/legal",
            json={"document_type": "privacy_policy", "version": "1.0", "content": "v1", "is_active": True},
            headers=admin_headers,
        )
        await async_client.post(
            "/api/admin/legal",
            json={"document_type": "privacy_policy", "version": "2.0", "content": "v2", "is_active": True},
            headers=admin_headers,
        )

        get_resp = await async_client.get("/api/legal/privacy_policy")
        assert get_resp.json()["version"] == "2.0"

        list_resp = await async_client.get("/api/admin/legal?document_type=privacy_policy", headers=admin_headers)
        versions = {d["version"]: d["is_active"] for d in list_resp.json()}
        assert versions == {"1.0": False, "2.0": True}

    async def test_accept_terms_records_acceptance(self, async_client: AsyncClient, auth_headers: dict, admin_headers: dict):
        await async_client.post(
            "/api/admin/legal",
            json={"document_type": "terms_of_use", "version": "1.0", "content": "Terms v1", "is_active": True},
            headers=admin_headers,
        )
        resp = await async_client.post(
            "/api/legal/accept",
            json={"document_type": "terms_of_use", "version": "1.0"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["document_type"] == "terms_of_use"
        assert data["version"] == "1.0"
        assert data["accepted_at"]

    async def test_accept_unpublished_version_404(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.post(
            "/api/legal/accept",
            json={"document_type": "terms_of_use", "version": "9.9"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
