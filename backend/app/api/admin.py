"""Admin panel API endpoints. Requires admin role."""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, text

from app.core.database import get_db
from app.core.security import get_current_admin, hash_password, create_access_token
from app.models.domain import (
    User, UserRole, Auction, AuctionStatus, Bid, Payment, Commission, SupportTicket,
)
from app.schemas.auth import UserResponse, TokenResponse
from app.schemas.auction import AuctionResponse

logger = logging.getLogger("bidmont")
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---- Auto-migration helper (raw SQL to avoid ORM column issues) ----
MISSING_COLUMNS_SQL = {
    "users": [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_terms BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_privacy BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_hash VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires_at TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    ],
    "auctions": [
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS brand VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS model VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS year INTEGER",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS mileage INTEGER",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS fuel_type VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS transmission VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS damage_status VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS equipment_brand VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS serial_number VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS condition VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS location VARCHAR",
        "ALTER TABLE auctions ADD COLUMN IF NOT EXISTS winner_user_id VARCHAR",
    ],
    "bids": [
        "ALTER TABLE bids ADD COLUMN IF NOT EXISTS ip_address VARCHAR",
    ],
    "payments": [
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    ],
    "support_tickets": [
        "ALTER TABLE support_tickets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    ],
}


async def run_migration_raw(db: AsyncSession):
    """Run raw ALTER TABLE migrations to add missing columns."""
    for table, statements in MISSING_COLUMNS_SQL.items():
        for sql in statements:
            try:
                await db.execute(text(sql))
                await db.commit()
                logger.info(f"Migration: executed on {table}")
            except Exception as e:
                await db.rollback()
                logger.warning(f"Migration: skipped on {table} ({e})")


# ---- Seed Admin (first-run only, uses raw SQL) ----
@admin_router.get("/seed", response_model=TokenResponse)
async def seed_admin(
    email: str = Query("admin@bidmont.me", description="Admin email"),
    password: str = Query("admin123", min_length=6, description="Admin password"),
    db: AsyncSession = Depends(get_db),
):
    """Create the first admin user. Only works if no admin exists yet."""
    # Step 1: Run migrations first
    await run_migration_raw(db)

    # Step 2: Check if any admin already exists (raw SQL to avoid ORM column mapping)
    result = await db.execute(text("SELECT id FROM users WHERE role = 'admin' LIMIT 1"))
    if result.first():
        raise HTTPException(status_code=400, detail="Admin user already exists")

    # Step 3: Check if email is taken
    result = await db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
    if result.first():
        raise HTTPException(status_code=400, detail="Email already in use")

    # Step 4: Create admin with raw SQL (only essential columns)
    admin_id = str(uuid.uuid4())
    password_hash_value = hash_password(password)
    now_str = "NOW()"

    await db.execute(
        text("""
            INSERT INTO users (id, name, email, password_hash, role, status, accepted_terms, accepted_privacy, marketing_consent, created_at, updated_at)
            VALUES (:id, :name, :email, :password_hash, :role, :status, :accepted_terms, :accepted_privacy, :marketing_consent, NOW(), NOW())
        """),
        {
            "id": admin_id,
            "name": "Admin",
            "email": email,
            "password_hash": password_hash_value,
            "role": "admin",
            "status": "active",
            "accepted_terms": True,
            "accepted_privacy": True,
            "marketing_consent": False,
        },
    )
    await db.commit()

    access_token = create_access_token(data={"sub": admin_id, "role": "admin"})

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=admin_id,
            name="Admin",
            email=email,
            phone=None,
            role="admin",
            status="active",
            created_at="",
        ),
    )


# ---- Users ----
@admin_router.get("/users", response_model=list[UserResponse])
async def admin_list_users(
    role: str | None = Query(None, description="Filter by role"),
    status: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with optional filters. Admin only."""
    query = select(User).order_by(desc(User.created_at))
    if role:
        query = query.where(User.role == UserRole(role))
    if status:
        query = query.where(User.status == status)

    result = await db.execute(query)
    users = result.scalars().all()
    return [
        UserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            phone=u.phone,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            status=u.status,
            created_at=str(u.created_at) if u.created_at else "",
        )
        for u in users
    ]


@admin_router.put("/users/{user_id}/status", response_model=UserResponse)
async def admin_update_user_status(
    user_id: str,
    new_status: str = Query(..., pattern=r"^(active|banned|suspended)$"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user status (active/banned/suspended). Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = new_status
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        status=user.status,
        created_at=str(user.created_at) if user.created_at else "",
    )


# ---- Auctions (all) ----
@admin_router.get("/auctions", response_model=list[AuctionResponse])
async def admin_list_auctions(
    status: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all auctions (including pending). Admin only."""
    from sqlalchemy.orm import selectinload

    query = select(Auction).options(selectinload(Auction.images)).order_by(desc(Auction.created_at))
    if status:
        query = query.where(Auction.status == AuctionStatus(status))

    result = await db.execute(query)
    auctions = result.scalars().all()

    return [
        AuctionResponse(
            id=a.id,
            seller_id=a.seller_id,
            category_id=a.category_id,
            title=a.title,
            description=a.description,
            start_price=a.start_price,
            current_price=a.current_price,
            min_increment=a.min_increment,
            start_time=a.start_time,
            end_time=a.end_time,
            status=a.status.value,
            winner_user_id=a.winner_user_id,
            created_at=a.created_at,
            brand=a.brand,
            model=a.model,
            year=a.year,
            mileage=a.mileage,
            fuel_type=a.fuel_type,
            transmission=a.transmission,
            damage_status=a.damage_status,
            equipment_brand=a.equipment_brand,
            serial_number=a.serial_number,
            condition=a.condition,
            location=a.location,
        )
        for a in auctions
    ]


# ---- Stats ----
@admin_router.get("/stats")
async def admin_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform statistics. Admin only."""
    # Total counts
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()

    result = await db.execute(select(func.count(Auction.id)))
    total_auctions = result.scalar()

    result = await db.execute(select(func.count(Bid.id)))
    total_bids = result.scalar()

    result = await db.execute(
        select(func.count(Auction.id)).where(Auction.status == AuctionStatus.active)
    )
    active_auctions = result.scalar()

    result = await db.execute(
        select(func.count(Auction.id)).where(Auction.status == AuctionStatus.completed)
    )
    completed_auctions = result.scalar()

    result = await db.execute(
        select(func.count(Auction.id)).where(Auction.status == AuctionStatus.pending_approval)
    )
    pending_auctions = result.scalar()

    # Payment/commission totals
    result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == "completed"
        )
    )
    total_revenue = float(result.scalar())

    result = await db.execute(
        select(func.coalesce(func.sum(Commission.amount), 0)).where(
            Commission.status == "completed"
        )
    )
    total_commissions = float(result.scalar())

    return {
        "total_users": total_users,
        "total_auctions": total_auctions,
        "total_bids": total_bids,
        "active_auctions": active_auctions,
        "completed_auctions": completed_auctions,
        "pending_auctions": pending_auctions,
        "total_revenue": total_revenue,
        "total_commissions": total_commissions,
    }