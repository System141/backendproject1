"""Integration tests for the bidding API endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import Auction, AuctionStatus, Category, Bid, User, UserRole
from app.models.base import Base
from app.core.security import create_access_token


class TestPlaceBid:
    async def test_place_bid_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        """POST /api/auctions/{id}/bids should place a valid bid."""
        # Create an active auction
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Biddable Auction",
            description="You can bid here",
            start_price=1000.0,
            current_price=1000.0,
            min_increment=50.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=7),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        # Create a buyer user (not the seller)
        buyer_id = str(uuid.uuid4())
        buyer = User(
            id=buyer_id,
            name="Buyer User",
            email=f"buyer_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(buyer)
        await db_session.commit()

        buyer_token = create_access_token(data={"sub": buyer.id, "role": buyer.role.value})
        buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

        payload = {"amount": 1100.0}
        response = await async_client.post(
            f"/api/auctions/{auction.id}/bids",
            json=payload,
            headers=buyer_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 1100.0
        assert data["auction_id"] == auction.id
        assert data["user_id"] == buyer.id

        # Verify current_price was updated on the auction
        await db_session.refresh(auction)
        assert auction.current_price == 1100.0

    async def test_seller_cannot_bid_own_auction(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        seller_headers: dict,
        test_category: Category,
    ):
        """Seller should get 403 when bidding on their own auction."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="My Own Auction",
            description="Cannot bid on this",
            start_price=500.0,
            current_price=500.0,
            min_increment=25.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(
            f"/api/auctions/{auction.id}/bids",
            json={"amount": 600.0},
            headers=seller_headers,
        )
        assert response.status_code == 403

    async def test_bid_below_minimum(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        """Bid below current_price + min_increment should return 400."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Min Bid Test",
            description="Test minimum bid",
            start_price=1000.0,
            current_price=1000.0,
            min_increment=100.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        buyer_id = str(uuid.uuid4())
        buyer = User(
            id=buyer_id,
            name="Buyer",
            email=f"buyer2_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(buyer)
        await db_session.commit()

        token = create_access_token(data={"sub": buyer.id, "role": buyer.role.value})
        headers = {"Authorization": f"Bearer {token}"}

        # 1050 < 1100 (1000 + 100) -> should fail
        response = await async_client.post(
            f"/api/auctions/{auction.id}/bids",
            json={"amount": 1050.0},
            headers=headers,
        )
        assert response.status_code == 400
        assert "minimum" in response.json()["detail"].lower()

    async def test_bid_on_ended_auction(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        """Bid on an ended auction should return 400."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Ended Auction",
            description="Already ended",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=10),
            end_time=datetime.now(timezone.utc) - timedelta(days=3),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        buyer_id = str(uuid.uuid4())
        buyer = User(
            id=buyer_id,
            name="Buyer3",
            email=f"buyer3_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(buyer)
        await db_session.commit()

        token = create_access_token(data={"sub": buyer.id, "role": buyer.role.value})
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.post(
            f"/api/auctions/{auction.id}/bids",
            json={"amount": 200.0},
            headers=headers,
        )
        assert response.status_code == 400
        assert "ended" in response.json()["detail"].lower()

    async def test_bid_on_pending_auction(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        """Bid on a pending (not yet active) auction should return 400."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Pending Auction",
            description="Not yet active",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.pending_approval,
        )
        db_session.add(auction)
        await db_session.commit()

        buyer_id = str(uuid.uuid4())
        buyer = User(
            id=buyer_id,
            name="Buyer4",
            email=f"buyer4_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(buyer)
        await db_session.commit()

        token = create_access_token(data={"sub": buyer.id, "role": buyer.role.value})
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.post(
            f"/api/auctions/{auction.id}/bids",
            json={"amount": 200.0},
            headers=headers,
        )
        assert response.status_code == 400
        assert "not active" in response.json()["detail"].lower()

    async def test_bid_unauthorized(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        """Unauthenticated user should get 401."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Auth Test",
            description="Need auth to bid",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(
            f"/api/auctions/{auction.id}/bids",
            json={"amount": 200.0},
        )
        assert response.status_code == 401


class TestBidHistory:
    async def test_bid_history(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        """GET /api/auctions/{id}/bids should return bid history."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="History Test",
            description="Check history",
            start_price=500.0,
            current_price=500.0,
            min_increment=25.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=7),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        # Create multiple bids from different users
        bids = []
        for i in range(3):
            buyer_id = str(uuid.uuid4())
            buyer = User(
                id=buyer_id,
                name=f"Bidder {i}",
                email=f"bidder_{i}_{uuid.uuid4().hex[:8]}@example.com",
                password_hash="$2b$12$dummyhash",
                role=UserRole.buyer,
                status="active",
                accepted_terms=True,
                accepted_privacy=True,
                marketing_consent=False,
            )
            db_session.add(buyer)
            await db_session.flush()

            bid = Bid(
                id=str(uuid.uuid4()),
                auction_id=auction.id,
                user_id=buyer.id,
                amount=500.0 + (i + 1) * 50.0,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=10 * i),
            )
            db_session.add(bid)
            bids.append(bid)
        await db_session.commit()

        response = await async_client.get(f"/api/auctions/{auction.id}/bids")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3
        # Bids should be ordered by amount descending
        amounts = [b["amount"] for b in data["bids"]]
        assert amounts == sorted(amounts, reverse=True)

    async def test_bid_history_empty(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        """Auction with no bids should return empty list."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="No Bids",
            description="No bids yet",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.get(f"/api/auctions/{auction.id}/bids")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["bids"] == []


class TestFinalizeAuction:
    async def test_finalize_with_winner(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        seller_headers: dict,
        test_category: Category,
    ):
        """POST /api/auctions/{id}/finalize should set winner from highest bid."""
        # Create an auction that has ended
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Finalize Test",
            description="Will be finalized",
            start_price=500.0,
            current_price=600.0,
            min_increment=25.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=10),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.flush()

        # Create a buyer and a bid
        buyer_id = str(uuid.uuid4())
        buyer = User(
            id=buyer_id,
            name="Winner",
            email=f"winner_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(buyer)
        await db_session.flush()

        bid = Bid(
            id=str(uuid.uuid4()),
            auction_id=auction.id,
            user_id=buyer.id,
            amount=600.0,
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        db_session.add(bid)
        await db_session.commit()

        response = await async_client.post(
            f"/api/auctions/{auction.id}/finalize",
            headers=seller_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["winner_user_id"] == buyer.id
        assert data["winning_bid"] == 600.0
        assert data["has_bids"] is True

        # Verify DB state
        await db_session.refresh(auction)
        assert auction.status == AuctionStatus.completed
        assert auction.winner_user_id == buyer.id

    async def test_finalize_no_bids(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        seller_headers: dict,
        test_category: Category,
    ):
        """Auction with no bids should complete with no winner."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="No Bids Finalize",
            description="Will finalize without winner",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=10),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(
            f"/api/auctions/{auction.id}/finalize",
            headers=seller_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["winner_user_id"] is None
        assert data["has_bids"] is False

    async def test_finalize_still_active(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        seller_headers: dict,
        test_category: Category,
    ):
        """Auction that hasn't ended yet should not be finalizable."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Still Running",
            description="Cannot finalize yet",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=3),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(
            f"/api/auctions/{auction.id}/finalize",
            headers=seller_headers,
        )
        assert response.status_code == 400
        assert "not ended" in response.json()["detail"].lower()

    async def test_buyer_cannot_finalize(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        auth_headers: dict,
        test_category: Category,
    ):
        """Only the seller or an admin should be able to finalize."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Unauthorized Finalize",
            description="Buyer cannot finalize",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=10),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(
            f"/api/auctions/{auction.id}/finalize",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestMyBids:
    async def test_my_bids(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        """GET /api/auctions/bids/my should return current user's bids."""
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="My Bids Auction",
            description="Check my bids",
            start_price=500.0,
            current_price=500.0,
            min_increment=25.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(days=7),
            status=AuctionStatus.active,
        )
        db_session.add(auction)
        await db_session.commit()

        # Create a buyer and make 2 bids
        buyer_id = str(uuid.uuid4())
        buyer = User(
            id=buyer_id,
            name="My Bidder",
            email=f"mybidder_{uuid.uuid4().hex[:8]}@example.com",
            password_hash="$2b$12$dummyhash",
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
            marketing_consent=False,
        )
        db_session.add(buyer)
        await db_session.flush()

        for i in range(2):
            bid = Bid(
                id=str(uuid.uuid4()),
                auction_id=auction.id,
                user_id=buyer.id,
                amount=500.0 + (i + 1) * 100.0,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=5 * i),
            )
            db_session.add(bid)
        await db_session.commit()

        token = create_access_token(data={"sub": buyer.id, "role": buyer.role.value})
        headers = {"Authorization": f"Bearer {token}"}

        response = await async_client.get("/api/auctions/bids/my", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(b["user_id"] == buyer.id for b in data)
