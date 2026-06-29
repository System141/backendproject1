"""Integration tests for payment API access rules."""
import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.domain import Auction, AuctionStatus, Category, User, UserRole


async def _create_buyer(db_session: AsyncSession, name: str = "Buyer") -> User:
    buyer = User(
        id=str(uuid.uuid4()),
        name=name,
        email=f"{name.lower()}_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="$2b$12$dummyhash",
        role=UserRole.buyer,
        status="active",
        accepted_terms=True,
        accepted_privacy=True,
        marketing_consent=False,
    )
    db_session.add(buyer)
    await db_session.flush()
    return buyer


def _headers_for(user: User) -> dict:
    token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


class TestCreatePayment:
    async def test_winner_can_create_pending_payment(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        winner = await _create_buyer(db_session, "Winner")
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Won Auction",
            description="Ready for payment",
            start_price=100.0,
            current_price=150.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=5),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status=AuctionStatus.completed,
            winner_user_id=winner.id,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(
            "/api/payments",
            json={"auction_id": auction.id},
            headers=_headers_for(winner),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["auction_id"] == auction.id
        assert data["buyer_id"] == winner.id
        assert data["amount"] == 150.0
        assert data["status"] == "pending"

    async def test_non_winner_cannot_pay(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        seller_user: User,
        test_category: Category,
    ):
        winner = await _create_buyer(db_session, "Winner")
        other_buyer = await _create_buyer(db_session, "OtherBuyer")
        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Wrong Buyer",
            description="Only winner can pay",
            start_price=100.0,
            current_price=150.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=5),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            status=AuctionStatus.completed,
            winner_user_id=winner.id,
        )
        db_session.add(auction)
        await db_session.commit()

        response = await async_client.post(
            "/api/payments",
            json={"auction_id": auction.id},
            headers=_headers_for(other_buyer),
        )

        assert response.status_code == 403
