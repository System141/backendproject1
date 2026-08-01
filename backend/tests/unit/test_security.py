"""Unit tests for the security module (password hashing, JWT tokens)."""
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt, JWTError

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_totp_secret,
    verify_totp,
    totp_otpauth_url,
    _hotp,
    JWT_SECRET,
    JWT_ALGORITHM,
)


class TestTotp:
    def test_hotp_matches_rfc4226_test_vectors(self):
        # RFC 4226 Appendix D: HOTP-SHA1 with the ASCII secret "12345678901234567890"
        import base64
        secret_b32 = base64.b32encode(b"12345678901234567890").decode()
        expected = ["755224", "287082", "359152", "969429", "338314"]
        for counter, code in enumerate(expected):
            assert _hotp(secret_b32, counter) == code

    def test_verify_totp_accepts_current_code(self):
        secret = generate_totp_secret()
        import time
        counter = int(time.time() // 30)
        code = _hotp(secret, counter)
        assert verify_totp(secret, code) is True

    def test_verify_totp_rejects_wrong_code(self):
        secret = generate_totp_secret()
        assert verify_totp(secret, "000000") is False

    def test_verify_totp_rejects_empty(self):
        assert verify_totp(generate_totp_secret(), "") is False
        assert verify_totp("", "123456") is False

    def test_otpauth_url_contains_secret_and_issuer(self):
        secret = generate_totp_secret()
        url = totp_otpauth_url(secret, "admin@bidmont.me")
        assert url.startswith("otpauth://totp/")
        assert secret in url
        assert "BidMont" in url


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = hash_password("my_secret_pass")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        hashed = hash_password("my_secret_pass")
        assert verify_password("my_secret_pass", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("my_secret_pass")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_different_each_time(self):
        pwd = "same_password"
        h1 = hash_password(pwd)
        h2 = hash_password(pwd)
        # bcrypt salts ensure different hashes
        assert h1 != h2
        # Both should still verify correctly
        assert verify_password(pwd, h1) is True
        assert verify_password(pwd, h2) is True


class TestCreateAccessToken:
    def test_basic_token_creation(self):
        token = create_access_token(data={"sub": "user123", "role": "buyer"})
        assert isinstance(token, str)
        # JWT has 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_token_contains_correct_payload(self):
        data = {"sub": "user123", "role": "admin", "custom": "value"}
        token = create_access_token(data=data)
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"
        assert payload["custom"] == "value"

    def test_token_has_expiration(self):
        token = create_access_token(data={"sub": "user1"})
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "exp" in payload
        assert isinstance(payload["exp"], int)

    def test_token_with_custom_expiry(self):
        short_lived = timedelta(minutes=5)
        token = create_access_token(data={"sub": "user1"}, expires_delta=short_lived)
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = exp - now
        assert timedelta(minutes=4) < diff < timedelta(minutes=6), f"diff={diff}"


class TestDecodeAccessToken:
    def test_decode_valid_token(self):
        token = create_access_token(data={"sub": "user1"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user1"

    def test_decode_invalid_token(self):
        payload = decode_access_token("this.is.not.a.valid.jwt")
        assert payload is None

    def test_decode_malformed_token(self):
        payload = decode_access_token("not-a-token")
        assert payload is None

    def test_decode_expired_token(self):
        # Create a token that expired 1 hour ago
        expired_delta = timedelta(hours=-1)
        token = create_access_token(
            data={"sub": "user1"}, expires_delta=expired_delta
        )
        payload = decode_access_token(token)
        assert payload is None

    def test_decode_token_with_wrong_secret(self):
        token = jwt.encode(
            {"sub": "user1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret",
            algorithm=JWT_ALGORITHM,
        )
        payload = decode_access_token(token)
        assert payload is None
