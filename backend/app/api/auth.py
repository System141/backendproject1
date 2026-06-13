import os
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.domain import User, UserRole
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check required privacy fields
    if not req.accepted_terms or not req.accepted_privacy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms and privacy policy.",
        )

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == req.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Check if phone already exists
    if req.phone:
        result = await db.execute(select(User).where(User.phone == req.phone))
        existing_phone = result.scalars().first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists.",
            )

    # Validate role
    try:
        role = UserRole(req.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {req.role}")

    # Create user
    user = User(
        id=str(uuid.uuid4()),
        name=req.name,
        email=req.email,
        phone=req.phone,
        password_hash=hash_password(req.password),
        role=role,
        status="active",
        accepted_terms=req.accepted_terms,
        accepted_privacy=req.accepted_privacy,
        marketing_consent=req.marketing_consent,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate JWT
    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
            status=user.status,
            created_at=str(user.created_at) if user.created_at else "",
        ),
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Find user by email
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active. Please contact support.",
        )

    # Generate JWT
    access_token = create_access_token(data={"sub": user.id, "role": user.role.value})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            role=user.role.value,
            status=user.status,
            created_at=str(user.created_at) if user.created_at else "",
        ),
    )


@auth_router.post("/forgot-password")
async def forgot_password(req: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    # Find user by email
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()

    if not user:
        # Don't reveal whether the email exists; return success anyway
        return {"message": "If the email exists, a reset link has been sent."}

    # Generate reset token (valid 1 hour)
    reset_token = str(uuid.uuid4())
    user.reset_token_hash = reset_token  # In production, hash this
    user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
    await db.commit()

    # In demo/dev mode, return the token directly so the reset form can be tested
    # In production, send an email with the reset link
    return {
        "message": "If the email exists, a reset link has been sent.",
        "reset_token": reset_token,  # Only returned in dev/demo mode
    }


@auth_router.post("/reset-password")
async def reset_password(req: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    # Find user by reset token
    result = await db.execute(
        select(User).where(
            User.reset_token_hash == req.token,
            User.reset_token_expires_at > datetime.utcnow(),
        )
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    # Update password
    user.password_hash = hash_password(req.new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    await db.commit()

    return {"message": "Password reset successfully."}