"""Integration tests for RBAC tiers (doc §17.1): Support must not be able to
touch credit package price or bid history, but can handle support tickets."""
import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.domain import SupportTicket, User, UserRole


async def _make_role_user(db_session: AsyncSession, role: UserRole) -> User:
    user = User(
        id=str(uuid.uuid4()),
        name=f"{role.value} user",
        email=f"{role.value}_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("StrongPass123!"),
        role=role,
        status="active",
        accepted_terms=True,
        accepted_privacy=True,
        marketing_consent=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _headers(user: User) -> dict:
    token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


class TestSupportRoleRestrictions:
    async def test_support_cannot_create_credit_package(self, async_client: AsyncClient, db_session: AsyncSession):
        support = await _make_role_user(db_session, UserRole.support)
        resp = await async_client.post(
            "/api/admin/credit-packages",
            json={"name": "Pack", "credits": 100, "price_eur": 10, "active": True, "sort_order": 1},
            headers=_headers(support),
        )
        assert resp.status_code == 403

    async def test_support_cannot_invalidate_bid(self, async_client: AsyncClient, db_session: AsyncSession):
        support = await _make_role_user(db_session, UserRole.support)
        resp = await async_client.post(
            f"/api/admin/bids/{uuid.uuid4()}/invalidate",
            json={"reason": "test"},
            headers=_headers(support),
        )
        assert resp.status_code == 403

    async def test_support_cannot_adjust_credits(self, async_client: AsyncClient, db_session: AsyncSession):
        support = await _make_role_user(db_session, UserRole.support)
        buyer = await _make_role_user(db_session, UserRole.buyer)
        resp = await async_client.post(
            "/api/admin/credits/adjust",
            json={"user_id": buyer.id, "amount": 10, "reason": "test"},
            headers=_headers(support),
        )
        assert resp.status_code == 403

    async def test_support_can_list_and_update_tickets(self, async_client: AsyncClient, db_session: AsyncSession):
        support = await _make_role_user(db_session, UserRole.support)
        ticket = SupportTicket(id=str(uuid.uuid4()), subject="Help", message="I need help", status="open")
        db_session.add(ticket)
        await db_session.commit()

        list_resp = await async_client.get("/api/admin/support-tickets", headers=_headers(support))
        assert list_resp.status_code == 200

        update_resp = await async_client.put(
            f"/api/admin/support-tickets/{ticket.id}?new_status=resolved", headers=_headers(support)
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "resolved"

    async def test_super_admin_has_admin_capability(self, async_client: AsyncClient, db_session: AsyncSession):
        super_admin = await _make_role_user(db_session, UserRole.super_admin)
        resp = await async_client.post(
            "/api/admin/credit-packages",
            json={"name": "Pack", "credits": 100, "price_eur": 10, "active": True, "sort_order": 1},
            headers=_headers(super_admin),
        )
        assert resp.status_code == 201
