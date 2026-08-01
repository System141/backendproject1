"""Integration tests for admin TOTP 2FA (doc §17.3)."""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import _hotp
from app.models.domain import User


async def _current_code(secret: str) -> str:
    import time
    return _hotp(secret, int(time.time() // 30))


class TestSetupAndEnable:
    async def test_status_starts_disabled(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.get("/api/admin/2fa/status", headers=admin_headers)
        assert response.status_code == 200
        assert response.json() == {"enabled": False}

    async def test_setup_returns_secret_and_otpauth_url(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.post("/api/admin/2fa/setup", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["secret"]
        assert data["otpauth_url"].startswith("otpauth://totp/")

    async def test_verify_with_correct_code_enables(self, async_client: AsyncClient, admin_headers: dict):
        setup = await async_client.post("/api/admin/2fa/setup", headers=admin_headers)
        secret = setup.json()["secret"]
        code = await _current_code(secret)

        response = await async_client.post("/api/admin/2fa/verify", json={"code": code}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "enabled"

        status_resp = await async_client.get("/api/admin/2fa/status", headers=admin_headers)
        assert status_resp.json() == {"enabled": True}

    async def test_verify_with_wrong_code_rejected(self, async_client: AsyncClient, admin_headers: dict):
        await async_client.post("/api/admin/2fa/setup", headers=admin_headers)
        response = await async_client.post("/api/admin/2fa/verify", json={"code": "000000"}, headers=admin_headers)
        assert response.status_code == 400

    async def test_verify_without_setup_rejected(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.post("/api/admin/2fa/verify", json={"code": "123456"}, headers=admin_headers)
        assert response.status_code == 400

    async def test_requires_staff_auth(self, async_client: AsyncClient, auth_headers: dict):
        response = await async_client.post("/api/admin/2fa/setup", headers=auth_headers)
        assert response.status_code == 403


class TestDisable:
    async def test_disable_with_correct_code(self, async_client: AsyncClient, admin_headers: dict):
        setup = await async_client.post("/api/admin/2fa/setup", headers=admin_headers)
        secret = setup.json()["secret"]
        await async_client.post("/api/admin/2fa/verify", json={"code": await _current_code(secret)}, headers=admin_headers)

        response = await async_client.post("/api/admin/2fa/disable", json={"code": await _current_code(secret)}, headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "disabled"

        status_resp = await async_client.get("/api/admin/2fa/status", headers=admin_headers)
        assert status_resp.json() == {"enabled": False}

    async def test_disable_without_enabling_rejected(self, async_client: AsyncClient, admin_headers: dict):
        response = await async_client.post("/api/admin/2fa/disable", json={"code": "123456"}, headers=admin_headers)
        assert response.status_code == 400


class TestLoginEnforcement:
    async def test_login_without_2fa_unaffected(self, async_client: AsyncClient, admin_user: User):
        response = await async_client.post("/api/auth/login", json={"email": admin_user.email, "password": "AdminPass123!"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_with_2fa_enabled_requires_code(self, async_client: AsyncClient, admin_headers: dict, admin_user: User):
        setup = await async_client.post("/api/admin/2fa/setup", headers=admin_headers)
        secret = setup.json()["secret"]
        await async_client.post("/api/admin/2fa/verify", json={"code": await _current_code(secret)}, headers=admin_headers)

        response = await async_client.post("/api/auth/login", json={"email": admin_user.email, "password": "AdminPass123!"})
        assert response.status_code == 401
        assert response.json()["detail"] == "TOTP code required"

    async def test_login_with_2fa_enabled_and_correct_code_succeeds(self, async_client: AsyncClient, admin_headers: dict, admin_user: User):
        setup = await async_client.post("/api/admin/2fa/setup", headers=admin_headers)
        secret = setup.json()["secret"]
        await async_client.post("/api/admin/2fa/verify", json={"code": await _current_code(secret)}, headers=admin_headers)

        response = await async_client.post("/api/auth/login", json={
            "email": admin_user.email, "password": "AdminPass123!", "totp_code": await _current_code(secret),
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_with_2fa_enabled_and_wrong_code_rejected(self, async_client: AsyncClient, admin_headers: dict, admin_user: User):
        setup = await async_client.post("/api/admin/2fa/setup", headers=admin_headers)
        secret = setup.json()["secret"]
        await async_client.post("/api/admin/2fa/verify", json={"code": await _current_code(secret)}, headers=admin_headers)

        response = await async_client.post("/api/auth/login", json={
            "email": admin_user.email, "password": "AdminPass123!", "totp_code": "000000",
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid TOTP code"
