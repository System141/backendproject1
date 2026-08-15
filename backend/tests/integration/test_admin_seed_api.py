"""POST /admin/seed - first-run admin bootstrap. Security regression: the
"already seeded" guard used to check `role = 'admin'` only, so a deployment
whose staff had all been promoted to super_admin (possible since
admin_update_user_role shipped) would slip past it and mint a fresh admin."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import User


@pytest.mark.asyncio
async def test_seed_requires_correct_secret(async_client: AsyncClient, monkeypatch):
    monkeypatch.setenv("SEED_SECRET", "right-secret")
    resp = await async_client.post("/api/admin/seed?email=a@b.com&password=Passw0rd1&secret=wrong-secret")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_seed_fails_closed_when_unset(async_client: AsyncClient, monkeypatch):
    monkeypatch.delenv("SEED_SECRET", raising=False)
    resp = await async_client.post("/api/admin/seed?email=a@b.com&password=Passw0rd1&secret=anything")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_seed_creates_first_admin(async_client: AsyncClient, monkeypatch):
    monkeypatch.setenv("SEED_SECRET", "right-secret")
    resp = await async_client.post("/api/admin/seed?email=first@bidmont.me&password=Passw0rd1&secret=right-secret")
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_seed_blocked_once_an_admin_exists(async_client: AsyncClient, db_session: AsyncSession, admin_user: User, monkeypatch):
    monkeypatch.setenv("SEED_SECRET", "right-secret")
    resp = await async_client.post("/api/admin/seed?email=second@bidmont.me&password=Passw0rd1&secret=right-secret")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_seed_blocked_when_only_a_super_admin_exists(async_client: AsyncClient, db_session: AsyncSession, super_admin_user: User, monkeypatch):
    """Regression: a staff roster of super_admin-only used to slip past the
    `role = 'admin'` guard and let /seed mint a second admin account."""
    monkeypatch.setenv("SEED_SECRET", "right-secret")
    resp = await async_client.post("/api/admin/seed?email=second@bidmont.me&password=Passw0rd1&secret=right-secret")
    assert resp.status_code == 400
