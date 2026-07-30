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
            "declaration_accepted": True,
        }
        response = await async_client.post("/api/auctions", json=payload, headers=seller_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Auction Vehicle"
        assert data["status"] == "under_review"
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
            "declaration_accepted": True,
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
            "declaration_accepted": True,
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
            status=AuctionStatus.under_review,
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
            status=AuctionStatus.live,
        )
        db_session.add_all([pending, active])
        await db_session.commit()

        response = await async_client.get("/api/auctions")
        assert response.status_code == 200
        data = response.json()
        titles = [a["title"] for a in data]
        assert "Active Auction" in titles
        assert "Pending Auction" not in titles

    async def test_total_count_header(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category
    ):
        for i in range(3):
            db_session.add(Auction(
                id=str(uuid.uuid4()), seller_id=seller_user.id, category_id=test_category.id,
                title=f"Count Test {i}", description="counting", start_price=100.0, current_price=100.0,
                min_increment=10.0, start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc) + timedelta(days=3), status=AuctionStatus.live,
            ))
        await db_session.commit()

        response = await async_client.get("/api/auctions?limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert int(response.headers["X-Total-Count"]) >= 3

    async def test_search_matches_lot_code_and_brand(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category
    ):
        db_session.add(Auction(
            id=str(uuid.uuid4()), seller_id=seller_user.id, category_id=test_category.id,
            title="Old Timer", description="a classic", brand="Volkswagen", model="Golf",
            location="Podgorica", lot_code="BM-VEH-000042",
            start_price=100.0, current_price=100.0, min_increment=10.0,
            start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.live,
        ))
        await db_session.commit()

        by_lot = await async_client.get("/api/auctions?search=BM-VEH-000042")
        assert any(a["title"] == "Old Timer" for a in by_lot.json())

        by_brand = await async_client.get("/api/auctions?search=Volkswagen")
        assert any(a["title"] == "Old Timer" for a in by_brand.json())

        by_city = await async_client.get("/api/auctions?city=Podgorica")
        assert any(a["title"] == "Old Timer" for a in by_city.json())


class TestAutocomplete:
    async def test_autocomplete_matches_brand(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category
    ):
        db_session.add(Auction(
            id=str(uuid.uuid4()), seller_id=seller_user.id, category_id=test_category.id,
            title="Suggest Me", description="autocomplete target", brand="Toyota", model="Corolla",
            location="Niksic", lot_code="BM-VEH-000099",
            start_price=100.0, current_price=100.0, min_increment=10.0,
            start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.live,
        ))
        await db_session.commit()

        resp = await async_client.get("/api/auctions/autocomplete?q=Toyo")
        assert resp.status_code == 200
        assert "Toyota" in resp.json()

    async def test_autocomplete_requires_min_length(self, async_client: AsyncClient):
        resp = await async_client.get("/api/auctions/autocomplete?q=a")
        assert resp.status_code == 422


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
            status=AuctionStatus.live,
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
            status=AuctionStatus.under_review,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(f"/api/auctions/{auction.id}/approve", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "live"

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
            status=AuctionStatus.under_review,
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
            status=AuctionStatus.under_review,
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
            status=AuctionStatus.live,
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


class TestContactUnlock:
    """Doc §12.5/§5.11 - AC-11/AC-12: seller/winner contact is hidden during
    a live auction and only revealed to the two authorized parties after it ends."""

    async def _make_ended_auction_with_winner(self, db_session, seller_user, test_category):
        winner_id = str(uuid.uuid4())
        winner = User(
            id=winner_id,
            name="Winner Buyer",
            email=f"winner_{uuid.uuid4().hex[:8]}@example.com",
            phone="+38267000111",
            password_hash="$2b$12$dummyhash",
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(winner)
        await db_session.flush()

        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Contact Unlock Test",
            description="Ended with a winner",
            start_price=500.0,
            current_price=600.0,
            min_increment=25.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=10),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status=AuctionStatus.ended,
            winner_user_id=winner_id,
        )
        db_session.add(auction)
        await db_session.commit()
        return auction, winner

    async def test_contact_hidden_while_live(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, seller_headers: dict, test_category: Category
    ):
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Still Live",
            description="Contact must stay hidden",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.live,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.get(f"/api/auctions/{auction.id}/contact", headers=seller_headers)
        assert response.status_code == 400

    async def test_seller_sees_winner_contact_after_end(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, seller_headers: dict, test_category: Category
    ):
        auction, winner = await self._make_ended_auction_with_winner(db_session, seller_user, test_category)

        response = await async_client.get(f"/api/auctions/{auction.id}/contact", headers=seller_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "winner"
        assert data["email"] == winner.email
        assert data["phone"] == winner.phone

    async def test_winner_sees_seller_contact_after_end(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category
    ):
        auction, winner = await self._make_ended_auction_with_winner(db_session, seller_user, test_category)
        token = create_access_token(data={"sub": winner.id, "role": winner.role.value})
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get(f"/api/auctions/{auction.id}/contact", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "seller"
        assert data["email"] == seller_user.email

    async def test_contact_forbidden_for_other_user(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, auth_headers: dict, test_category: Category
    ):
        auction, _winner = await self._make_ended_auction_with_winner(db_session, seller_user, test_category)

        response = await async_client.get(f"/api/auctions/{auction.id}/contact", headers=auth_headers)
        assert response.status_code == 403

    async def test_contact_no_winner_returns_404(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, seller_headers: dict, test_category: Category
    ):
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Ended No Bids",
            description="No winner to contact",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=10),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status=AuctionStatus.ended,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.get(f"/api/auctions/{auction.id}/contact", headers=seller_headers)
        assert response.status_code == 404