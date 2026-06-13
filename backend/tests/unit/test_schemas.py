"""Unit tests for Pydantic schemas (request/response validation)."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.schemas.user import UserUpdateRequest


class TestRegisterRequest:
    def test_valid_register_request(self):
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "StrongPass1!",
            "role": "buyer",
            "accepted_terms": True,
            "accepted_privacy": True,
            "marketing_consent": False,
        }
        req = RegisterRequest(**data)
        assert req.name == "John Doe"
        assert req.email == "john@example.com"
        assert req.role == "buyer"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError) as exc:
            RegisterRequest()
        errors = {e["loc"][0]: e["type"] for e in exc.value.errors()}
        assert "name" in errors
        assert "email" in errors
        assert "password" in errors

    def test_invalid_email_format(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name="Test",
                email="not-an-email",
                password="password123",
            )

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name="Test",
                email="test@example.com",
                password="12345",  # min_length=6
            )

    def test_password_too_long(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name="Test",
                email="test@example.com",
                password="x" * 129,  # max_length=128
            )

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name="Test",
                email="test@example.com",
                password="password123",
                role="superadmin",
            )

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name="",
                email="test@example.com",
                password="password123",
            )

    def test_valid_roles_accepted(self):
        for role in ("buyer", "seller", "corporate_seller", "admin"):
            req = RegisterRequest(
                name="Test",
                email=f"test_{role}@example.com",
                password="password123",
                role=role,
            )
            assert req.role == role

    def test_optional_phone(self):
        req = RegisterRequest(
            name="Test",
            email="test@example.com",
            password="password123",
            phone="+38267123456",
        )
        assert req.phone == "+38267123456"

    def test_default_marketing_consent_false(self):
        req = RegisterRequest(
            name="Test",
            email="test@example.com",
            password="password123",
        )
        assert req.marketing_consent is False


class TestLoginRequest:
    def test_valid_login(self):
        req = LoginRequest(email="test@example.com", password="mypassword")
        assert req.email == "test@example.com"
        assert req.password == "mypassword"

    def test_missing_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(password="mypassword")

    def test_missing_password(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="test@example.com")


class TestPasswordResetRequest:
    def test_valid_email(self):
        req = PasswordResetRequest(email="user@example.com")
        assert req.email == "user@example.com"

    def test_missing_email(self):
        with pytest.raises(ValidationError):
            PasswordResetRequest()


class TestPasswordResetConfirm:
    def test_valid_reset(self):
        req = PasswordResetConfirm(token="abc123", new_password="NewStrongPass1!")
        assert req.token == "abc123"
        assert req.new_password == "NewStrongPass1!"

    def test_new_password_too_short(self):
        with pytest.raises(ValidationError):
            PasswordResetConfirm(token="abc123", new_password="short")

    def test_missing_token(self):
        with pytest.raises(ValidationError):
            PasswordResetConfirm(new_password="NewStrongPass1!")


class TestUserResponse:
    def test_valid_response(self):
        data = {
            "id": "some-uuid",
            "name": "John",
            "email": "john@example.com",
            "role": "buyer",
            "status": "active",
            "created_at": "2024-01-01 00:00:00",
        }
        resp = UserResponse(**data)
        assert resp.id == "some-uuid"
        assert resp.phone is None  # optional

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            UserResponse()

    def test_with_phone(self):
        data = {
            "id": "uuid",
            "name": "John",
            "email": "john@example.com",
            "phone": "+38267123456",
            "role": "seller",
            "status": "active",
            "created_at": "2024-01-01T00:00:00",
        }
        resp = UserResponse(**data)
        assert resp.phone == "+38267123456"


class TestTokenResponse:
    def test_valid_token_response(self):
        user_data = {
            "id": "uuid-1",
            "name": "John",
            "email": "john@example.com",
            "role": "buyer",
            "status": "active",
            "created_at": "2024-01-01",
        }
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "user": user_data,
        }
        resp = TokenResponse(**data)
        assert resp.access_token == "eyJhbGciOiJIUzI1NiIs..."
        assert resp.token_type == "bearer"
        assert resp.user.name == "John"
        assert resp.user.email == "john@example.com"

    def test_missing_user(self):
        with pytest.raises(ValidationError):
            TokenResponse(access_token="some-token")


class TestUserUpdateRequest:
    def test_valid_update_all_fields(self):
        req = UserUpdateRequest(
            name="New Name",
            phone="+38267123456",
            marketing_consent=True,
        )
        assert req.name == "New Name"
        assert req.phone == "+38267123456"
        assert req.marketing_consent is True

    def test_empty_update(self):
        # All fields optional — empty body is valid for partial updates
        req = UserUpdateRequest()
        assert req.name is None
        assert req.phone is None
        assert req.marketing_consent is None

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            UserUpdateRequest(name="x" * 101)

    def test_phone_too_long(self):
        with pytest.raises(ValidationError):
            UserUpdateRequest(phone="x" * 21)