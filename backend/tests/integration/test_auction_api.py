"""Integration tests for the auction API endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Auction, AuctionStatus, Category, User, UserRole
from app.core.security import create_access_token


class TestCreateAuction:
    async def test_seller_creates_auction(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        """POST /api/auctions should create auction with pending status."""
        payload = {
            "title": "Test Auction Vehicle",
            "description": "A nice car for auction",
            "category_id": test_category.id,
            "start_price": 5000.0,
            "min_increment": 100.0,
            "end_time": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "brand": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "mileage": 50000,
            "fuel_type": "Petrol",
            "transmission": "Automatic",
        }
        response = await async_client.post("/api/auctions", json=payload, headers=seller_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Auction Vehicle"
        assert data["status"] == "pending_approval"
        assert data["start_price"] == 5000.0
        assert data["current_price"] == 5000.0
        assert data["brand"] == "Toyota"
        assert data["model"] == "Corolla"
        assert data["year"] == 2020

    async def test_buyer_cannot_create_auction(
        self, async_client: AsyncClient, auth_headers: dict, test_category: Category
    ):
        """Buyer should get 403 when trying to create auction."""
        payload = {
            "title": "Test Auction",
            "description": "A test item",
            "category_id": test_category.id,
            "start_price": 100.0,
            "min_increment": 10.0,
            "end_time": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        }
        response = await async_client.post("/api/auctions", json=payload, headers=auth_headers)
        assert response.status_code == 403

    async def test_invalid_category(
        self, async_client: AsyncClient, seller_headers: dict
    ):
        """Non-existent category should return 404."""
        payload = {
            "title": "Test",
            "description": "Test description here",
            "category_id": 99999,
            "start_price": 100.0,
            "min_increment": 10.0,
            "end_time": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        }
        response = await async_client.post("/api/auctions", json=payload, headers=seller_headers)
        assert response.status_code == 404

    async def test_past_end_time(
        self, async_client: AsyncClient, seller_headers: dict, test_category: Category
    ):
        """Past end_time should return 400."""
        payload = {
            "title": "Late Auction",
            "description": "Already ended",
            "category_id": test_category.id,
            "start_price": 100.0,
            "min_increment": 10.0,
            "end_time": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        }
        response = await async_client.post("/api/auctions", json=payload, headers=seller_headers)
        assert response.status_code == 400
        assert "future" in response.json()["detail"].lower()


class TestListAuctions:
    async def test_list_active_auctions(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category
    ):
        """GET /api/auctions should return active & completed auctions."""
        # Create a pending auction (should NOT be visible)
        pending = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Pending Auction",
            description="Not visible yet",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.pending_approval,
        )
        # Create an active auction (should be visible)
        active = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Active Auction",
            description="Visible to public",
            start_price=200.0,
            current_price=200.0,
            min_increment=20.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.active,
        )
        db_session.add_all([pending, active])
        await db_session.commit()

        response = await async_client.get("/api/auctions")
        assert response.status_code == 200
        data = response.json()
        titles = [a["title"] for a in data]
        assert "Active Auction" in titles
        assert "Pending Auction" not in titles


class TestAuctionDetail:
    async def test_get_auction_detail(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category
    ):
        """GET /api/auctions/{id} should return full details."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Detail Test",
            description="Check detail page",
            start_price=300.0,
            current_price=300.0,
            min_increment=30.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=5),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.get(f"/api/auctions/{auction.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Detail Test"
        assert data["category"] is not None
        assert data["category"]["name"] == "Vehicles"

    async def test_auction_not_found(self, async_client: AsyncClient):
        """Non-existent ID should return 404."""
        response = await async_client.get(f"/api/auctions/{uuid.uuid4()}")
        assert response.status_code == 404


class TestApproveReject:
    async def test_admin_approves_auction(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, admin_headers: dict, test_category: Category
    ):
        """Admin can approve a pending auction -> active."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Approve Me",
            description="Will be approved",
            start_price=500.0,
            current_price=500.0,
            min_increment=50.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=7),
            status=AuctionStatus.pending_approval,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(f"/api/auctions/{auction.id}/approve", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    async def test_admin_rejects_auction(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, admin_headers: dict, test_category: Category
    ):
        """Admin can reject a pending auction -> cancelled."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Reject Me",
            description="Will be rejected",
            start_price=500.0,
            current_price=500.0,
            min_increment=50.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=7),
            status=AuctionStatus.pending_approval,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(f"/api/auctions/{auction.id}/reject", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    async def test_seller_cannot_approve(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, seller_headers: dict, test_category: Category
    ):
        """Seller trying to approve should get 403."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="No Approve",
            description="Seller cannot approve",
            start_price=500.0,
            current_price=500.0,
            min_increment=50.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=7),
            status=AuctionStatus.pending_approval,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(f"/api/auctions/{auction.id}/approve", headers=seller_headers)
        assert response.status_code == 403


class TestMyAuctions:
    async def test_my_auctions(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, seller_headers: dict, test_category: Category
    ):
        """GET /api/auctions/my should return seller's own auctions."""
        for i in range(3):
            auction = Auction(
                id=str(uuid.uuid4()),
                seller_id=seller_user.id,
                category_id=test_category.id,
                title=f"My Auction {i}",
                description=f"Description {i}",
                start_price=100.0 * (i + 1),
                current_price=100.0 * (i + 1),
                min_increment=10.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=7),
            status=AuctionStatus.active,
            )
            db_session.add(auction)
        await db_session.commit()

        response = await async_client.get("/api/auctions/my", headers=seller_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(a["seller_id"] == seller_user.id for a in data)

    async def test_my_auctions_unauthorized(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Buyer should get 403 on /api/auctions/my."""
        response = await async_client.get("/api/auctions/my", headers=auth_headers)
        assert response.status_code == 403