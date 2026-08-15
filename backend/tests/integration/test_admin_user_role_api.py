"""Admin user-role management. Staff-tier roles (admin/super_admin/support)
are privilege-escalation-adjacent, so touching one on either side of the
change is gated to super_admin - see admin_update_user_role."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import User, UserRole


@pytest.mark.asyncio
async def test_admin_promotes_buyer_to_seller(async_client: AsyncClient, db_session: AsyncSession, test_user: User, admin_headers: dict):
    """A regular admin can freely move a user between non-staff roles."""
    resp = await async_client.put(f"/api/admin/users/{test_user.id}/role?new_role=seller", headers=admin_headers)

    assert resp.status_code == 200
    assert resp.json()["role"] == "seller"
    await db_session.refresh(test_user)
    assert test_user.role == UserRole.seller


@pytest.mark.asyncio
async def test_regular_admin_cannot_grant_admin_role(async_client: AsyncClient, db_session: AsyncSession, test_user: User, admin_headers: dict):
    """A regular admin trying to mint a new admin must be rejected (403), not silently allowed."""
    resp = await async_client.put(f"/api/admin/users/{test_user.id}/role?new_role=admin", headers=admin_headers)

    assert resp.status_code == 403
    await db_session.refresh(test_user)
    assert test_user.role == UserRole.buyer  # unchanged


@pytest.mark.asyncio
async def test_regular_admin_cannot_demote_an_admin(async_client: AsyncClient, db_session: AsyncSession, admin_headers: dict, super_admin_user: User):
    """Stripping an existing staff member's role is just as gated as granting one."""
    resp = await async_client.put(f"/api/admin/users/{super_admin_user.id}/role?new_role=buyer", headers=admin_headers)

    assert resp.status_code == 403
    await db_session.refresh(super_admin_user)
    assert super_admin_user.role == UserRole.super_admin  # unchanged


@pytest.mark.asyncio
async def test_super_admin_can_grant_admin_role(async_client: AsyncClient, db_session: AsyncSession, test_user: User, super_admin_headers: dict):
    resp = await async_client.put(f"/api/admin/users/{test_user.id}/role?new_role=admin", headers=super_admin_headers)

    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"
    await db_session.refresh(test_user)
    assert test_user.role == UserRole.admin


@pytest.mark.asyncio
async def test_admin_cannot_change_own_role(async_client: AsyncClient, db_session: AsyncSession, admin_user: User, admin_headers: dict):
    resp = await async_client.put(f"/api/admin/users/{admin_user.id}/role?new_role=buyer", headers=admin_headers)

    assert resp.status_code == 400
    await db_session.refresh(admin_user)
    assert admin_user.role == UserRole.admin  # unchanged


@pytest.mark.asyncio
async def test_super_admin_cannot_change_own_role(async_client: AsyncClient, db_session: AsyncSession, super_admin_user: User, super_admin_headers: dict):
    resp = await async_client.put(f"/api/admin/users/{super_admin_user.id}/role?new_role=admin", headers=super_admin_headers)

    assert resp.status_code == 400
    await db_session.refresh(super_admin_user)
    assert super_admin_user.role == UserRole.super_admin  # unchanged


@pytest.mark.asyncio
async def test_update_role_rejects_invalid_role(async_client: AsyncClient, test_user: User, admin_headers: dict):
    resp = await async_client.put(f"/api/admin/users/{test_user.id}/role?new_role=superuser", headers=admin_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_role_requires_admin(async_client: AsyncClient, test_user: User, auth_headers: dict):
    resp = await async_client.put(f"/api/admin/users/{test_user.id}/role?new_role=seller", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_role_404_for_missing_user(async_client: AsyncClient, admin_headers: dict):
    resp = await async_client.put("/api/admin/users/does-not-exist/role?new_role=seller", headers=admin_headers)
    assert resp.status_code == 404
