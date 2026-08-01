"""Integration tests for the auth API endpoints."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import User, UserRole
from app.core.security import hash_password, create_access_token


class TestRegister:
    async def test_successful_registration(self, async_client: AsyncClient, test_user_data: dict):
        """POST /api/auth/register should create user and return token."""
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["name"] == test_user_data["name"]
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["role"] == "buyer"

    async def test_duplicate_email(self, async_client: AsyncClient, test_user_data: dict):
        """Registering with the same email should return 409."""
        await async_client.post("/api/auth/register", json=test_user_data)
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_missing_terms(self, async_client: AsyncClient, test_user_data: dict):
        """Missing accepted_terms should return 400."""
        test_user_data.pop("accepted_terms", None)
        test_user_data["accepted_privacy"] = True
        # Need to set accepted_terms explicitly to False (not missing)
        test_user_data["accepted_terms"] = False
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "terms" in response.json()["detail"].lower()

    async def test_missing_privacy(self, async_client: AsyncClient, test_user_data: dict):
        """Missing accepted_privacy should return 400."""
        test_user_data["accepted_terms"] = True
        test_user_data["accepted_privacy"] = False
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "privacy" in response.json()["detail"].lower()

    async def test_invalid_email(self, async_client: AsyncClient, test_user_data: dict):
        """Invalid email format should return 422."""
        test_user_data["email"] = "not-an-email"
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 422

    async def test_weak_password(self, async_client: AsyncClient, test_user_data: dict):
        """Password too short should return 422."""
        test_user_data["password"] = "ab"
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 422

    async def test_duplicate_phone(self, async_client: AsyncClient, test_user_data: dict):
        """Registering with the same phone number should return 409."""
        phone = "+38267123456"
        test_user_data["phone"] = phone
        await async_client.post("/api/auth/register", json=test_user_data)

        # Second registration with same phone, different email
        data2 = {**test_user_data, "email": f"other_{uuid.uuid4().hex[:8]}@example.com"}
        response = await async_client.post("/api/auth/register", json=data2)
        assert response.status_code == 409
        assert "phone" in response.json()["detail"].lower()

    async def test_invalid_role(self, async_client: AsyncClient, test_user_data: dict):
        """Invalid role should return 400."""
        test_user_data["role"] = "superadmin"
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code in (400, 422)

    async def test_create_seller_account(self, async_client: AsyncClient, test_user_data: dict):
        """Register as seller should succeed."""
        test_user_data["role"] = "seller"
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        assert response.json()["user"]["role"] == "seller"


class TestLogin:
    async def test_successful_login(self, async_client: AsyncClient, test_user_data: dict):
        """POST /api/auth/login should return token for valid credentials."""
        # First register
        await async_client.post("/api/auth/register", json=test_user_data)

        # Then login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        response = await async_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_user_data["email"]

    async def test_login_wrong_password(self, async_client: AsyncClient, test_user_data: dict):
        """Wrong password should return 401."""
        await async_client.post("/api/auth/register", json=test_user_data)
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword",
        }
        response = await async_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Non-existent email should return 401."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepass123",
        }
        response = await async_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401

    async def test_login_inactive_user(self, async_client: AsyncClient, db_session: AsyncSession):
        """Inactive user should get 403."""
        import uuid as uuid_lib
        uid = str(uuid_lib.uuid4())
        user = User(
            id=uid,
            name="Inactive",
            email=f"inactive_{uuid_lib.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.buyer,
            status="inactive",  # Inactive account
            accepted_terms=True,
            accepted_privacy=True,
        )
        db_session.add(user)
        await db_session.commit()

        login_data = {
            "email": user.email,
            "password": "TestPass123!",
        }
        response = await async_client.post("/api/auth/login", json=login_data)
        assert response.status_code == 403
        assert "not active" in response.json()["detail"].lower()

    async def test_missing_email(self, async_client: AsyncClient):
        """Missing email should return 422."""
        response = await async_client.post("/api/auth/login", json={"password": "test"})
        assert response.status_code == 422


class TestForgotPassword:
    async def test_forgot_password_existing_user(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Forgot password for existing user should return success message and token."""
        import uuid as uuid_lib
        user = User(
            id=str(uuid_lib.uuid4()),
            name="FP User",
            email=f"fp_{uuid_lib.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await async_client.post(
            "/api/auth/forgot-password",
            json={"email": user.email},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reset_token" in data  # Dev mode returns token

    async def test_forgot_password_nonexistent_user(self, async_client: AsyncClient):
        """Non-existent email should still return 200 (security)."""
        response = await async_client.post(
            "/api/auth/forgot-password",
            json={"email": "unknown@example.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Should still return success message without revealing user existence


class TestResetPassword:
    async def test_successful_reset(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Reset password with valid token should succeed."""
        import uuid as uuid_lib
        user = User(
            id=str(uuid_lib.uuid4()),
            name="Reset User",
            email=f"reset_{uuid_lib.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Get reset token
        fp_response = await async_client.post(
            "/api/auth/forgot-password",
            json={"email": user.email},
        )
        reset_token = fp_response.json()["reset_token"]

        # Reset password
        response = await async_client.post(
            "/api/auth/reset-password",
            json={"token": reset_token, "new_password": "NewStrongPass456!"},
        )
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()

    async def test_reset_with_invalid_token(self, async_client: AsyncClient):
        """Invalid token should return 400."""
        response = await async_client.post(
            "/api/auth/reset-password",
            json={"token": "invalid-token", "new_password": "NewStrongPass456!"},
        )
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    async def test_reset_with_short_password(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """New password too short should return 422."""
        import uuid as uuid_lib
        user = User(
            id=str(uuid_lib.uuid4()),
            name="Short Reset User",
            email=f"shortreset_{uuid_lib.uuid4().hex[:8]}@example.com",
            password_hash=hash_password("TestPass123!"),
            role=UserRole.buyer,
            status="active",
            accepted_terms=True,
            accepted_privacy=True,
        )
        db_session.add(user)
        await db_session.commit()

        fp_response = await async_client.post(
            "/api/auth/forgot-password",
            json={"email": user.email},
        )
        reset_token = fp_response.json()["reset_token"]

        response = await async_client.post(
            "/api/auth/reset-password",
            json={"token": reset_token, "new_password": "ab"},
        )
        assert response.status_code == 422


class TestEmailVerification:
    """Doc §20 AC-01: new user registers, verifies contact info, buys credits."""

    async def test_register_starts_unverified_and_returns_dev_token(
        self, async_client: AsyncClient, test_user_data: dict,
    ):
        response = await async_client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email_verified"] is False
        assert data["email_verification_token"]  # dev-mode convenience, same as forgot-password's reset_token

    async def test_verify_email_with_valid_token(
        self, async_client: AsyncClient, test_user_data: dict, db_session: AsyncSession,
    ):
        register_response = await async_client.post("/api/auth/register", json=test_user_data)
        token = register_response.json()["email_verification_token"]

        response = await async_client.post("/api/auth/verify-email", json={"token": token})
        assert response.status_code == 200

        result = await db_session.execute(select(User).where(User.email == test_user_data["email"]))
        user = result.scalars().first()
        assert user.email_verified is True
        assert user.email_verification_token_hash is None

    async def test_verify_email_with_invalid_token(self, async_client: AsyncClient):
        response = await async_client.post("/api/auth/verify-email", json={"token": "not-a-real-token"})
        assert response.status_code == 400

    async def test_verify_email_token_is_single_use(
        self, async_client: AsyncClient, test_user_data: dict,
    ):
        register_response = await async_client.post("/api/auth/register", json=test_user_data)
        token = register_response.json()["email_verification_token"]

        first = await async_client.post("/api/auth/verify-email", json={"token": token})
        assert first.status_code == 200
        second = await async_client.post("/api/auth/verify-email", json={"token": token})
        assert second.status_code == 400

    async def test_resend_verification_requires_auth(self, async_client: AsyncClient):
        response = await async_client.post("/api/auth/resend-verification")
        assert response.status_code in (401, 403)

    async def test_resend_verification_issues_new_usable_token(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db_session: AsyncSession,
    ):
        test_user.email_verified = False
        await db_session.commit()

        response = await async_client.post("/api/auth/resend-verification", headers=auth_headers)
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

        await db_session.refresh(test_user)
        assert test_user.email_verification_token_hash is not None
        assert test_user.email_verified is False

    async def test_resend_verification_noop_when_already_verified(
        self, async_client: AsyncClient, auth_headers: dict, test_user: User, db_session: AsyncSession,
    ):
        test_user.email_verified = True
        await db_session.commit()

        response = await async_client.post("/api/auth/resend-verification", headers=auth_headers)
        assert response.status_code == 200
        assert "already verified" in response.json()["message"].lower()


class TestGetMe:
    async def test_get_me_authenticated(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """GET /api/users/me should return current user profile."""
        response = await async_client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert data["role"] == "buyer"

    async def test_get_me_unauthenticated(self, async_client: AsyncClient):
        """No auth header should return 401."""
        response = await async_client.get("/api/users/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, async_client: AsyncClient):
        """Invalid token should return 401."""
        headers = {"Authorization": "Bearer invalidtoken"}
        response = await async_client.get("/api/users/me", headers=headers)
        assert response.status_code == 401


class TestUpdateMe:
    async def test_update_name(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """PUT /api/users/me should update user name."""
        response = await async_client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    async def test_update_phone(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Update phone number."""
        response = await async_client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"phone": "+38267123456"},
        )
        assert response.status_code == 200
        assert response.json()["phone"] == "+38267123456"

    async def test_update_marketing_consent(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Update marketing consent."""
        response = await async_client.put(
            "/api/users/me",
            headers=auth_headers,
            json={"marketing_consent": True},
        )
        assert response.status_code == 200
        assert response.json() is not None

    async def test_update_unauthenticated(self, async_client: AsyncClient):
        """No auth should return 401."""
        response = await async_client.put(
            "/api/users/me",
            json={"name": "Hacker"},
        )
        assert response.status_code == 401

    async def test_update_empty_body(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Empty body is allowed (partial update)."""
        response = await async_client.put(
            "/api/users/me",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 200