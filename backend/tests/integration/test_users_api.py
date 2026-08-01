"""Integration tests for the /api/users endpoints."""
import uuid
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.domain import Auction, AuctionStatus, Category, User


class TestSellerStats:
    """Doc §11.3: Seller Dashboard Overview needs Draft/Under Review/Live/Ended counts."""

    async def test_counts_by_status_bucket(
        self, async_client: AsyncClient, seller_headers: dict, seller_user: User,
        test_category: Category, db_session: AsyncSession,
    ):
        statuses = [
            AuctionStatus.draft, AuctionStatus.draft,
            AuctionStatus.under_review,
            AuctionStatus.live,
            AuctionStatus.ended,
        ]
        for i, status in enumerate(statuses):
            db_session.add(Auction(
                id=str(uuid.uuid4()),
                seller_id=seller_user.id,
                category_id=test_category.id,
                title=f"Stats auction {i}",
                description="desc for stats test",
                start_price=100.0,
                current_price=120.0,
                min_increment=10.0,
                start_time=datetime.now(timezone.utc) - timedelta(days=1),
                end_time=datetime.now(timezone.utc) + timedelta(days=1),
                status=status,
            ))
        await db_session.commit()

        response = await async_client.get("/api/users/me/seller-stats", headers=seller_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["draft_auctions"] == 2
        assert data["pending_auctions"] == 1
        assert data["active_auctions"] == 1
        assert data["completed_auctions"] == 1
        assert data["total_auctions"] == 5


class TestChangePassword:
    async def test_successful_change(self, async_client: AsyncClient, auth_headers: dict, test_user: User, db_session: AsyncSession):
        response = await async_client.put(
            "/api/users/me/password",
            json={"current_password": "TestPass123!", "new_password": "NewPass456!"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # The endpoint commits through a separate session (test client override);
        # this session's identity map still holds the stale pre-change object
        # (expire_on_commit=False), so it must be force-refreshed before reading.
        await db_session.refresh(test_user)
        assert verify_password("NewPass456!", test_user.password_hash)
        assert not verify_password("TestPass123!", test_user.password_hash)

    async def test_wrong_current_password(self, async_client: AsyncClient, auth_headers: dict):
        response = await async_client.put(
            "/api/users/me/password",
            json={"current_password": "WrongPass!", "new_password": "NewPass456!"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    async def test_requires_auth(self, async_client: AsyncClient):
        response = await async_client.put(
            "/api/users/me/password",
            json={"current_password": "x", "new_password": "NewPass456!"},
        )
        assert response.status_code in (401, 403)

    async def test_new_password_too_short(self, async_client: AsyncClient, auth_headers: dict):
        response = await async_client.put(
            "/api/users/me/password",
            json={"current_password": "TestPass123!", "new_password": "abc"},
            headers=auth_headers,
        )
        assert response.status_code == 422
