"""Integration tests for the /api/users endpoints."""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.domain import User


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
