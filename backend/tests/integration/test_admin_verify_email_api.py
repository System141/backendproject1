"""Admin manual email-verify stopgap (until corporate SMTP is live)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import User


@pytest.mark.asyncio
async def test_admin_verifies_user_email(async_client: AsyncClient, db_session: AsyncSession, test_user: User, admin_headers: dict):
    test_user.email_verified = False
    await db_session.commit()

    resp = await async_client.post(f"/api/admin/users/{test_user.id}/verify-email", headers=admin_headers)

    assert resp.status_code == 200
    assert resp.json()["email_verified"] is True
    await db_session.refresh(test_user)
    assert test_user.email_verified is True


@pytest.mark.asyncio
async def test_verify_email_requires_admin(async_client: AsyncClient, test_user: User, auth_headers: dict):
    resp = await async_client.post(f"/api/admin/users/{test_user.id}/verify-email", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_verify_email_404_for_missing_user(async_client: AsyncClient, admin_headers: dict):
    resp = await async_client.post("/api/admin/users/does-not-exist/verify-email", headers=admin_headers)
    assert resp.status_code == 404
