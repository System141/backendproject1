import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote

import bcrypt as _bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.domain import User, UserRole

# ---- Configuration ----
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = _bcrypt.gensalt()
    return _bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return _bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---- TOTP (doc §17.3: admin 2FA) ----
# RFC 6238 TOTP implemented against stdlib only (hmac/hashlib/struct/base64) -
# no pyotp/qrcode dependency needed for a 6-digit, 30s-step code.
TOTP_STEP_SECONDS = 30
TOTP_DIGITS = 6


def generate_totp_secret() -> str:
    """Random 160-bit base32 secret (RFC 4226 recommended key length)."""
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii")


def _hotp(secret_b32: str, counter: int) -> str:
    key = base64.b32decode(secret_b32.upper())
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10 ** TOTP_DIGITS)
    return str(code_int).zfill(TOTP_DIGITS)


def verify_totp(secret_b32: str, code: str, valid_window: int = 1) -> bool:
    """Check `code` against the current 30s time-step, tolerating clock
    drift of up to `valid_window` steps either side."""
    if not secret_b32 or not code:
        return False
    counter = int(time.time() // TOTP_STEP_SECONDS)
    code = code.strip()
    return any(
        hmac.compare_digest(_hotp(secret_b32, counter + offset), code)
        for offset in range(-valid_window, valid_window + 1)
    )


def totp_otpauth_url(secret_b32: str, account_email: str, issuer: str = "BidMont") -> str:
    """otpauth:// URI so any standard authenticator app (Google Authenticator,
    Authy, ...) can add the account by scanning/pasting - no QR image
    generation needed client-side, the app can render a QR from this URI or
    the admin can type the raw secret in manually."""
    label = quote(f"{issuer}:{account_email}")
    return f"otpauth://totp/{label}?secret={secret_b32}&issuer={quote(issuer)}&digits={TOTP_DIGITS}&period={TOTP_STEP_SECONDS}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that returns the current authenticated User or raises 401."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[dict]:
    """Dependency that returns user data from token if present, or None."""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None
    return payload


def require_role(*roles: UserRole):
    """Factory that returns a dependency requiring one of the given roles."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return role_checker


async def get_current_seller(
    current_user: User = Depends(require_role(UserRole.seller, UserRole.corporate_seller)),
) -> User:
    """Dependency: current user must be a seller or corporate_seller."""
    return current_user


async def get_current_admin(
    current_user: User = Depends(require_role(UserRole.admin, UserRole.super_admin)),
) -> User:
    """Dependency: current user must be admin or super_admin. This is the
    gate for sensitive financial/credit/bid/user-management actions (doc
    §17.1) - `support` is deliberately NOT included here, so a new sensitive
    endpoint is support-blocked by default unless it explicitly opts in via
    get_current_staff instead."""
    return current_user


async def get_current_staff(
    current_user: User = Depends(require_role(UserRole.admin, UserRole.super_admin, UserRole.support)),
) -> User:
    """Dependency: current user must be any staff tier, including support.
    Use only for read-only/ticket-handling endpoints the doc explicitly
    lists as within Support's remit (doc §17.1) - never for credit package
    price, bid history, or other financial/audit mutations."""
    return current_user