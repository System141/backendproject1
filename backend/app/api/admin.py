"""Admin panel API endpoints. Requires admin role."""
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc, func, text

from app.core.database import get_db
from app.core.security import get_current_admin, hash_password, create_access_token
from app.core.migrations import run_migration_raw
from app.models.domain import (
    User, UserRole, Auction, AuctionStatus, Bid, Payment, Commission, SupportTicket,
    Category, AuditLog,
)
from app.schemas.auth import UserResponse, TokenResponse
from app.schemas.auction import AuctionResponse
from app.schemas.bid import BidResponse
from app.schemas.category import CategoryResponse, CategoryCreate, CategoryUpdate
from app.schemas.payment import PaymentResponse, CommissionResponse
from app.schemas.support import SupportTicketResponse

logger = logging.getLogger("bidmont")
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---- Audit log helper ----
async def _log_audit(db: AsyncSession, admin_id: str, action: str, entity_type: str, entity_id: str | None = None, details: str | None = None):
    log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=admin_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    await db.commit()


# ---- Seed Admin (first-run only, uses raw SQL) ----
@admin_router.post("/seed", response_model=TokenResponse)
async def seed_admin(
    email: str = Query("admin@bidmont.me", description="Admin email"),
    password: str = Query(..., min_length=6, description="Admin password"),
    secret: str = Query(..., description="Must match SEED_SECRET env var"),
    db: AsyncSession = Depends(get_db),
):
    """Create the first admin user. Requires SEED_SECRET env var match."""
    seed_secret = os.getenv("SEED_SECRET")
    if not seed_secret or secret != seed_secret:
        raise HTTPException(status_code=403, detail="Invalid seed secret")

    await run_migration_raw(db)

    result = await db.execute(text("SELECT id FROM users WHERE role = 'admin' LIMIT 1"))
    if result.first():
        raise HTTPException(status_code=400, detail="Admin user already exists")

    result = await db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
    if result.first():
        raise HTTPException(status_code=400, detail="Email already in use")

    admin_id = str(uuid.uuid4())
    password_hash_value = hash_password(password)

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


# ===================== USERS =====================
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

    await _log_audit(db, current_user.id, "update_user_status", "user", user_id, f"Status changed to {new_status}")

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        status=user.status,
        created_at=str(user.created_at) if user.created_at else "",
    )


# ===================== CATEGORIES =====================
@admin_router.get("/categories", response_model=list[CategoryResponse])
async def admin_list_categories(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all categories. Admin only."""
    result = await db.execute(select(Category).order_by(asc(Category.id)))
    categories = result.scalars().all()
    return categories


@admin_router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_category(
    req: CategoryCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new category. Admin only."""
    existing = await db.execute(select(Category).where(Category.slug == req.slug))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Category slug already exists")

    category = Category(
        name=req.name,
        slug=req.slug,
        parent_id=req.parent_id,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)

    await _log_audit(db, current_user.id, "create_category", "category", str(category.id), f"Created category '{req.name}'")
    return category


@admin_router.put("/categories/{category_id}", response_model=CategoryResponse)
async def admin_update_category(
    category_id: int,
    req: CategoryUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a category. Admin only."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    await _log_audit(db, current_user.id, "update_category", "category", str(category_id), f"Updated category fields: {list(update_data.keys())}")
    return category


@admin_router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_category(
    category_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete (soft-deactivate) a category. Admin only."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.status = "inactive"
    await db.commit()

    await _log_audit(db, current_user.id, "delete_category", "category", str(category_id), f"Deactivated category '{category.name}'")


# ===================== AUCTIONS =====================
@admin_router.get("/auctions", response_model=list[AuctionResponse])
async def admin_list_auctions(
    status: str | None = Query(None, description="Filter by status"),
    featured: bool | None = Query(None, description="Filter by featured"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all auctions. Admin only."""
    from sqlalchemy.orm import selectinload

    query = select(Auction).options(selectinload(Auction.images)).order_by(desc(Auction.created_at))
    if status:
        query = query.where(Auction.status == AuctionStatus(status))
    if featured is not None:
        query = query.where(Auction.is_featured == featured)

    result = await db.execute(query)
    auctions = result.scalars().all()

    def build(a):
        return AuctionResponse(
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
            is_featured=bool(a.is_featured) if hasattr(a, 'is_featured') else False,
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

    return [build(a) for a in auctions]


@admin_router.put("/auctions/{auction_id}/featured", response_model=AuctionResponse)
async def admin_toggle_featured(
    auction_id: str,
    is_featured: bool = Query(..., description="Set featured status"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Toggle featured status for an auction. Admin only."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Auction).options(selectinload(Auction.images)).where(Auction.id == auction_id)
    )
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    auction.is_featured = is_featured
    await db.commit()
    await db.refresh(auction)

    await _log_audit(db, current_user.id, "toggle_featured", "auction", auction_id, f"Featured set to {is_featured}")

    return AuctionResponse(
        id=auction.id,
        seller_id=auction.seller_id,
        category_id=auction.category_id,
        title=auction.title,
        description=auction.description,
        start_price=auction.start_price,
        current_price=auction.current_price,
        min_increment=auction.min_increment,
        start_time=auction.start_time,
        end_time=auction.end_time,
        status=auction.status.value,
        winner_user_id=auction.winner_user_id,
        is_featured=bool(auction.is_featured) if hasattr(auction, 'is_featured') else False,
        created_at=auction.created_at,
        brand=auction.brand,
        model=auction.model,
        year=auction.year,
        mileage=auction.mileage,
        fuel_type=auction.fuel_type,
        transmission=auction.transmission,
        damage_status=auction.damage_status,
        equipment_brand=auction.equipment_brand,
        serial_number=auction.serial_number,
        condition=auction.condition,
        location=auction.location,
    )


# ===================== BIDS =====================
@admin_router.get("/bids", response_model=list[BidResponse])
async def admin_list_bids(
    auction_id: str | None = Query(None, description="Filter by auction ID"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all bids with optional filters. Admin only."""
    query = select(Bid).order_by(desc(Bid.created_at))
    if auction_id:
        query = query.where(Bid.auction_id == auction_id)
    if user_id:
        query = query.where(Bid.user_id == user_id)

    result = await db.execute(query)
    bids = result.scalars().all()

    return [
        BidResponse(
            id=b.id,
            auction_id=b.auction_id,
            user_id=b.user_id,
            amount=b.amount,
            created_at=b.created_at,
        )
        for b in bids
    ]


# ===================== SUPPORT TICKETS =====================
@admin_router.get("/support-tickets", response_model=list[SupportTicketResponse])
async def admin_list_tickets(
    status: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all support tickets with optional status filter. Admin only."""
    query = select(SupportTicket).order_by(desc(SupportTicket.created_at))
    if status:
        query = query.where(SupportTicket.status == status)

    result = await db.execute(query)
    tickets = result.scalars().all()
    return [
        SupportTicketResponse(
            id=t.id,
            user_id=t.user_id or "",
            subject=t.subject,
            message=t.message,
            status=t.status,
            created_at=str(t.created_at) if t.created_at else "",
            updated_at=str(t.updated_at) if t.updated_at else "",
        )
        for t in tickets
    ]


@admin_router.put("/support-tickets/{ticket_id}", response_model=SupportTicketResponse)
async def admin_update_ticket(
    ticket_id: str,
    new_status: str = Query(..., pattern=r"^(open|in_progress|resolved|closed)$"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update support ticket status. Admin only."""
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = new_status
    await db.commit()
    await db.refresh(ticket)

    await _log_audit(db, current_user.id, "update_ticket", "support_ticket", ticket_id, f"Status changed to {new_status}")

    return SupportTicketResponse(
        id=ticket.id,
        user_id=ticket.user_id or "",
        subject=ticket.subject,
        message=ticket.message,
        status=ticket.status,
        created_at=str(ticket.created_at) if ticket.created_at else "",
        updated_at=str(ticket.updated_at) if ticket.updated_at else "",
    )


# ===================== COMMISSIONS =====================
@admin_router.put("/commissions/{commission_id}/status", response_model=CommissionResponse)
async def admin_update_commission_status(
    commission_id: str,
    new_status: str = Query(..., pattern=r"^(pending|completed|failed|refunded)$"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update commission status. Admin only."""
    result = await db.execute(select(Commission).where(Commission.id == commission_id))
    commission = result.scalars().first()
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")

    from app.models.domain import PaymentStatus
    commission.status = PaymentStatus(new_status)
    await db.commit()
    await db.refresh(commission)

    await _log_audit(db, current_user.id, "update_commission_status", "commission", commission_id, f"Status changed to {new_status}")

    return CommissionResponse(
        id=commission.id,
        auction_id=commission.auction_id,
        seller_id=commission.seller_id,
        amount=commission.amount,
        rate=commission.rate,
        status=commission.status.value if hasattr(commission.status, 'value') else str(commission.status),
        created_at=str(commission.created_at) if commission.created_at else "",
    )


# ===================== AUDIT LOGS =====================
@admin_router.get("/audit-logs")
async def admin_list_audit_logs(
    action: str | None = Query(None, description="Filter by action"),
    entity_type: str | None = Query(None, description="Filter by entity type"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with optional filters. Admin only."""
    query = select(AuditLog).order_by(desc(AuditLog.created_at))
    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)

    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": str(log.created_at) if log.created_at else "",
        }
        for log in logs
    ]


# ===================== STATS =====================
@admin_router.get("/stats")
async def admin_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Platform statistics. Admin only."""
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