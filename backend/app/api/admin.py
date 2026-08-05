"""Admin panel API endpoints. Requires admin role."""
import os
import uuid
import string as string_module
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, desc, asc, func, text

from app.core.database import get_db
from app.core.security import (
    get_current_admin, get_current_staff, hash_password, create_access_token,
    generate_totp_secret, verify_totp, totp_otpauth_url,
)
from app.core.migrations import run_migration_raw
from app.models.domain import (
    User, UserRole, Auction, AuctionStatus, BIDDABLE_STATUSES, Bid, CreditPurchase, PaymentStatus, SupportTicket,
    Category, AuditLog, CreditPackage, BidIncrementRule, PlatformSettings, AuctionParticipant, AuctionImage,
    CreditLedgerType, TermsDocument, SellerProfile, SellerVerificationStatus, NotificationTemplate, _utcnow,
)
from app.schemas.auth import UserResponse, TokenResponse, TotpSetupResponse, TotpCodeRequest, TotpStatusResponse
from app.schemas.auction import AuctionResponse, AuctionImageResponse
from app.schemas.bid import BidResponse
from app.schemas.category import CategoryResponse, CategoryCreate, CategoryUpdate
from app.schemas.credit import (
    CreditPackageResponse, CreditPackageCreate, CreditPackageUpdate,
    BidIncrementRuleResponse, BidIncrementRuleCreate, BidIncrementRuleUpdate,
    PlatformSettingsResponse, PlatformSettingsUpdate,
    CreditAdjustRequest, CreditLedgerEntryResponse, ReasonRequest,
)
from app.schemas.support import SupportTicketResponse
from app.schemas.legal import TermsDocumentResponse, TermsDocumentCreate
from app.schemas.seller import SellerProfileResponse
from app.schemas.notification import NotificationTemplateResponse, NotificationTemplateUpdate
from app.services.auctions import build_auction_response, build_auction_image_response, get_or_create_settings
from app.services.credits import apply_ledger_entry
from app.services.notifications import send_notification, NotificationType, TEMPLATABLE_NOTIFICATION_TYPES

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


def _diff_summary(obj, update_data: dict) -> str:
    """Doc §17.2: audit entries need a before/after summary, not just which
    fields changed. Call BEFORE applying update_data's values to obj."""
    parts = [f"{field}: {getattr(obj, field)!r}->{value!r}" for field, value in update_data.items()]
    return "; ".join(parts) if parts else "(no fields changed)"


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
            email_verified=u.email_verified,
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

    old_status = user.status
    user.status = new_status
    await db.commit()
    await db.refresh(user)

    await _log_audit(db, current_user.id, "update_user_status", "user", user_id, f"status: {old_status!r}->{new_status!r}")

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        status=user.status,
        email_verified=user.email_verified,
        created_at=str(user.created_at) if user.created_at else "",
    )


@admin_router.post("/users/{user_id}/verify-email", response_model=UserResponse)
async def admin_verify_user_email(
    user_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually mark a user's email as verified. Stopgap until corporate
    SMTP is live and the self-service verify-email flow can actually
    deliver mail. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    await db.commit()
    await db.refresh(user)

    await _log_audit(db, current_user.id, "verify_user_email", "user", user_id, f"manually verified {user.email}")

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        status=user.status,
        email_verified=user.email_verified,
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
    summary = _diff_summary(category, update_data)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    await _log_audit(db, current_user.id, "update_category", "category", str(category_id), summary)
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


# ===================== CREDIT PACKAGES =====================
@admin_router.get("/credit-packages", response_model=list[CreditPackageResponse])
async def admin_list_credit_packages(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all credit packages (including inactive). Admin only."""
    result = await db.execute(select(CreditPackage).order_by(asc(CreditPackage.sort_order)))
    return result.scalars().all()


@admin_router.post("/credit-packages", response_model=CreditPackageResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_credit_package(
    req: CreditPackageCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a credit package. Admin only."""
    package = CreditPackage(
        id=str(uuid.uuid4()),
        name=req.name,
        credits=req.credits,
        price_eur=req.price_eur,
        active=req.active,
        sort_order=req.sort_order,
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)

    await _log_audit(db, current_user.id, "create_credit_package", "credit_package", package.id, f"Created package '{req.name}'")
    return package


@admin_router.put("/credit-packages/{package_id}", response_model=CreditPackageResponse)
async def admin_update_credit_package(
    package_id: str,
    req: CreditPackageUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a credit package. Admin only."""
    result = await db.execute(select(CreditPackage).where(CreditPackage.id == package_id))
    package = result.scalars().first()
    if not package:
        raise HTTPException(status_code=404, detail="Credit package not found")

    update_data = req.model_dump(exclude_unset=True)
    summary = _diff_summary(package, update_data)
    for field, value in update_data.items():
        setattr(package, field, value)

    await db.commit()
    await db.refresh(package)

    await _log_audit(db, current_user.id, "update_credit_package", "credit_package", package_id, summary)
    return package


# ===================== BID INCREMENT RULES =====================
@admin_router.get("/bid-increment-rules", response_model=list[BidIncrementRuleResponse])
async def admin_list_bid_increment_rules(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List bid increment rules. Admin only."""
    result = await db.execute(select(BidIncrementRule).order_by(asc(BidIncrementRule.min_price)))
    return result.scalars().all()


@admin_router.post("/bid-increment-rules", response_model=BidIncrementRuleResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_bid_increment_rule(
    req: BidIncrementRuleCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a bid increment rule (min_price threshold -> increment). Admin only."""
    rule = BidIncrementRule(min_price=req.min_price, increment=req.increment, sort_order=req.sort_order)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    await _log_audit(db, current_user.id, "create_bid_increment_rule", "bid_increment_rule", str(rule.id), f"min_price={req.min_price} increment={req.increment}")
    return rule


@admin_router.put("/bid-increment-rules/{rule_id}", response_model=BidIncrementRuleResponse)
async def admin_update_bid_increment_rule(
    rule_id: int,
    req: BidIncrementRuleUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a bid increment rule. Admin only."""
    result = await db.execute(select(BidIncrementRule).where(BidIncrementRule.id == rule_id))
    rule = result.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Bid increment rule not found")

    update_data = req.model_dump(exclude_unset=True)
    summary = _diff_summary(rule, update_data)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)

    await _log_audit(db, current_user.id, "update_bid_increment_rule", "bid_increment_rule", str(rule_id), summary)
    return rule


@admin_router.delete("/bid-increment-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_bid_increment_rule(
    rule_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a bid increment rule. Admin only."""
    result = await db.execute(select(BidIncrementRule).where(BidIncrementRule.id == rule_id))
    rule = result.scalars().first()
    if not rule:
        raise HTTPException(status_code=404, detail="Bid increment rule not found")

    await db.delete(rule)
    await db.commit()

    await _log_audit(db, current_user.id, "delete_bid_increment_rule", "bid_increment_rule", str(rule_id), None)


# ===================== PLATFORM SETTINGS =====================
@admin_router.get("/settings", response_model=PlatformSettingsResponse)
async def admin_get_settings(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get anti-sniping / default participation-cost settings. Admin only."""
    return await get_or_create_settings(db)


@admin_router.put("/settings", response_model=PlatformSettingsResponse)
async def admin_update_settings(
    req: PlatformSettingsUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update anti-sniping / default participation-cost settings. Admin only."""
    settings = await get_or_create_settings(db)
    update_data = req.model_dump(exclude_unset=True)
    summary = _diff_summary(settings, update_data)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    await _log_audit(db, current_user.id, "update_settings", "platform_settings", "1", summary)
    return settings


# ===================== CREDIT LEDGER / ADJUSTMENTS =====================
@admin_router.post("/credits/adjust", response_model=CreditLedgerEntryResponse)
async def admin_adjust_credits(
    req: CreditAdjustRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Manually adjust a user's credit balance. Reason is mandatory and audit-logged."""
    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    entry = await apply_ledger_entry(
        db, user, req.amount, CreditLedgerType.admin_adjust,
        reference=None, reason=req.reason, actor_id=current_user.id,
    )
    await db.commit()
    await db.refresh(entry)

    await _log_audit(db, current_user.id, "adjust_credits", "user", user.id, f"{req.amount:+.2f} credits: {req.reason}")
    return entry


# ===================== SELLER APPLICATIONS =====================
@admin_router.get("/sellers", response_model=list[SellerProfileResponse])
async def admin_list_seller_applications(
    verification_status: str | None = Query(None, description="Filter by pending/verified/rejected"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List seller applications (doc §11.3/§17). Admin only."""
    query = select(SellerProfile).order_by(desc(SellerProfile.created_at))
    if verification_status:
        query = query.where(SellerProfile.verification_status == SellerVerificationStatus(verification_status))
    result = await db.execute(query)
    return result.scalars().all()


@admin_router.post("/sellers/{profile_id}/verify", response_model=SellerProfileResponse)
async def admin_verify_seller(
    profile_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Approve a seller application. Also promotes the user's role to 'seller'
    if they registered as a buyer - role alone (doc's existing self-declared
    seller/corporate_seller registration) is not enough to publish LIVE
    listings without this verification (doc §11.1/§11.5).
    """
    result = await db.execute(select(SellerProfile).where(SellerProfile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Seller application not found")
    if profile.verification_status == SellerVerificationStatus.verified:
        raise HTTPException(status_code=400, detail="Already verified")

    profile.verification_status = SellerVerificationStatus.verified
    profile.rejection_reason = None
    profile.reviewed_by = current_user.id
    profile.reviewed_at = _utcnow()

    user_result = await db.execute(select(User).where(User.id == profile.user_id))
    user = user_result.scalars().first()
    if user and user.role not in (UserRole.seller, UserRole.corporate_seller):
        user.role = UserRole.corporate_seller if profile.account_type == "company" else UserRole.seller

    await db.commit()
    await db.refresh(profile)

    await send_notification(
        db, profile.user_id, NotificationType.seller_verified,
        "Seller application approved",
        "Your seller application has been verified. You can now create listings.",
        send_email=True,
        title_me="Prijava za prodavca odobrena",
        message_me="Vaša prijava za prodavca je verifikovana. Sada možete kreirati oglase.",
    )
    await _log_audit(db, current_user.id, "verify_seller", "seller_profile", profile.id, f"user {profile.user_id} verified")
    return profile


@admin_router.post("/sellers/{profile_id}/reject", response_model=SellerProfileResponse)
async def admin_reject_seller(
    profile_id: str,
    req: ReasonRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reject a seller application. Reason is mandatory and audit-logged."""
    result = await db.execute(select(SellerProfile).where(SellerProfile.id == profile_id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Seller application not found")
    if profile.verification_status == SellerVerificationStatus.verified:
        raise HTTPException(status_code=400, detail="Already verified - cannot reject")

    profile.verification_status = SellerVerificationStatus.rejected
    profile.rejection_reason = req.reason
    profile.reviewed_by = current_user.id
    profile.reviewed_at = _utcnow()
    await db.commit()
    await db.refresh(profile)

    await send_notification(
        db, profile.user_id, NotificationType.seller_rejected,
        "Seller application rejected",
        f"Your seller application was rejected: {req.reason}",
        send_email=True,
        title_me="Prijava za prodavca odbijena",
        message_me=f"Vaša prijava za prodavca je odbijena: {req.reason}",
    )
    await _log_audit(db, current_user.id, "reject_seller", "seller_profile", profile.id, req.reason)
    return profile


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

    query = (
        select(Auction)
        .options(selectinload(Auction.images), selectinload(Auction.seller).selectinload(User.seller_profile))
        .order_by(desc(Auction.created_at))
    )
    if status:
        query = query.where(Auction.status == AuctionStatus(status))
    if featured is not None:
        query = query.where(Auction.is_featured == featured)

    result = await db.execute(query)
    auctions = result.scalars().all()

    return [build_auction_response(a) for a in auctions]


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
        select(Auction)
        .options(selectinload(Auction.images), selectinload(Auction.seller).selectinload(User.seller_profile))
        .where(Auction.id == auction_id)
    )
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    auction.is_featured = is_featured
    await db.commit()
    await db.refresh(auction, attribute_names=["is_featured"])

    await _log_audit(db, current_user.id, "toggle_featured", "auction", auction_id, f"Featured set to {is_featured}")

    return build_auction_response(auction)


@admin_router.put("/auction-images/{image_id}/visibility", response_model=AuctionImageResponse)
async def admin_set_image_visibility(
    image_id: str,
    visibility: str = Query(..., pattern="^(public|private)$"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Doc §6.2: "Public/private erişim seviyesi admin'den ayarlanabilsin" -
    the only way a document (or image) becomes public/private. Admin only."""
    result = await db.execute(select(AuctionImage).where(AuctionImage.id == image_id))
    img = result.scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="File not found")

    old_visibility = img.visibility
    img.visibility = visibility
    await db.commit()
    await db.refresh(img)

    await _log_audit(db, current_user.id, "set_image_visibility", "auction_image", image_id, f"visibility: {old_visibility!r}->{visibility!r}")

    return build_auction_image_response(img)


@admin_router.post("/auctions/{auction_id}/cancel", response_model=AuctionResponse)
async def admin_cancel_auction(
    auction_id: str,
    req: ReasonRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a pending/active auction and reverse participation credits for
    everyone who joined it. Reason is mandatory and audit-logged. Reversal
    is a new +credit ledger entry, never an edit to the original spend.
    """
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Auction)
        .options(selectinload(Auction.images), selectinload(Auction.seller).selectinload(User.seller_profile))
        .where(Auction.id == auction_id)
    )
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status not in (AuctionStatus.draft, AuctionStatus.under_review, AuctionStatus.upcoming) + BIDDABLE_STATUSES:
        raise HTTPException(status_code=400, detail="Only not-yet-ended auctions can be cancelled")

    auction.status = AuctionStatus.cancelled

    participants_result = await db.execute(
        select(AuctionParticipant).where(AuctionParticipant.auction_id == auction_id)
    )
    participants = participants_result.scalars().all()
    for participant in participants:
        user_result = await db.execute(select(User).where(User.id == participant.user_id))
        participant_user = user_result.scalars().first()
        if participant_user:
            await apply_ledger_entry(
                db, participant_user, participant.credits_spent, CreditLedgerType.reversal,
                reference=auction_id, reason=req.reason, actor_id=current_user.id,
            )

    await db.commit()
    await db.refresh(auction, attribute_names=["status"])

    for participant in participants:
        await send_notification(
            db, participant.user_id,
            NotificationType.auction_cancelled,
            f"Auction cancelled: {auction.title}",
            f"'{auction.title}' was cancelled by the admin. Your {participant.credits_spent:.0f} participation credits have been reversed.",
            auction_id=auction_id,
            send_email=True,
            title_me=f"Aukcija otkazana: {auction.title}",
            message_me=f"'{auction.title}' je otkazana od strane administratora. Vaših {participant.credits_spent:.0f} kredita za učešće je vraćeno.",
        )

    await _log_audit(db, current_user.id, "cancel_auction", "auction", auction_id, req.reason)

    return build_auction_response(auction)


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


@admin_router.post("/bids/{bid_id}/invalidate", response_model=BidResponse)
async def admin_invalidate_bid(
    bid_id: str,
    req: ReasonRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a bid invalid (never deleted). Reason mandatory and audit-logged.
    If this was the highest valid bid, the auction's current_price is
    recomputed from the remaining valid bids.
    """
    result = await db.execute(select(Bid).where(Bid.id == bid_id))
    bid = result.scalars().first()
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    if bid.invalidated:
        raise HTTPException(status_code=400, detail="Bid is already invalidated")

    bid.invalidated = True
    bid.invalidated_reason = req.reason
    bid.invalidated_by = current_user.id
    bid.invalidated_at = _utcnow()

    auction_result = await db.execute(select(Auction).where(Auction.id == bid.auction_id).with_for_update())
    auction = auction_result.scalars().first()
    if auction:
        highest_result = await db.execute(
            select(Bid)
            .where(Bid.auction_id == auction.id, Bid.invalidated == False, Bid.id != bid.id)  # noqa: E712
            .order_by(desc(Bid.amount), asc(Bid.created_at))
            .limit(1)
        )
        highest = highest_result.scalars().first()
        auction.current_price = highest.amount if highest else auction.start_price

    await db.commit()
    await db.refresh(bid)

    await _log_audit(db, current_user.id, "invalidate_bid", "bid", bid_id, req.reason)

    return BidResponse(
        id=bid.id,
        auction_id=bid.auction_id,
        user_id=bid.user_id,
        amount=bid.amount,
        created_at=bid.created_at,
    )


# ===================== SUPPORT TICKETS =====================
@admin_router.get("/support-tickets", response_model=list[SupportTicketResponse])
async def admin_list_tickets(
    status: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """List all support tickets with optional status filter. Staff (admin/super_admin/support)."""
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
            category=t.category,
            lot_code=t.lot_code,
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
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Update support ticket status. Staff (admin/super_admin/support)."""
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_status = ticket.status
    ticket.status = new_status
    await db.commit()
    await db.refresh(ticket)

    await _log_audit(db, current_user.id, "update_ticket", "support_ticket", ticket_id, f"status: {old_status!r}->{new_status!r}")

    return SupportTicketResponse(
        id=ticket.id,
        user_id=ticket.user_id or "",
        subject=ticket.subject,
        message=ticket.message,
        category=ticket.category,
        lot_code=ticket.lot_code,
        status=ticket.status,
        created_at=str(ticket.created_at) if ticket.created_at else "",
        updated_at=str(ticket.updated_at) if ticket.updated_at else "",
    )


# ===================== LEGAL DOCUMENTS =====================
@admin_router.get("/legal", response_model=list[TermsDocumentResponse])
async def admin_list_legal_documents(
    document_type: str | None = Query(None, description="Filter by document type"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all legal document versions (doc §15/§17 - legal document version
    management). Admin only."""
    query = select(TermsDocument).order_by(desc(TermsDocument.created_at))
    if document_type:
        query = query.where(TermsDocument.document_type == document_type)
    result = await db.execute(query)
    return result.scalars().all()


@admin_router.post("/legal", response_model=TermsDocumentResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_legal_document(
    req: TermsDocumentCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish a new version of a legal document. Rows are never edited or
    deleted - a new version is a new row, and activating it deactivates any
    previously active version of the same type so GET /api/legal/{type}
    always resolves to exactly one document.
    """
    if req.is_active:
        prior = await db.execute(
            select(TermsDocument).where(
                TermsDocument.document_type == req.document_type,
                TermsDocument.is_active == True,  # noqa: E712
            )
        )
        for doc in prior.scalars().all():
            doc.is_active = False

    document = TermsDocument(
        id=str(uuid.uuid4()),
        document_type=req.document_type,
        version=req.version,
        content=req.content,
        is_active=req.is_active,
    )
    db.add(document)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f"Version {req.version} of {req.document_type} already exists")
    await db.refresh(document)

    await _log_audit(db, current_user.id, "create_legal_document", "terms_document", document.id, f"{req.document_type} v{req.version}")
    return document


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
        select(func.count(Auction.id)).where(Auction.status.in_(BIDDABLE_STATUSES))
    )
    active_auctions = result.scalar()

    result = await db.execute(
        select(func.count(Auction.id)).where(Auction.status == AuctionStatus.ended)
    )
    completed_auctions = result.scalar()

    result = await db.execute(
        select(func.count(Auction.id)).where(Auction.status == AuctionStatus.under_review)
    )
    pending_auctions = result.scalar()

    result = await db.execute(
        select(func.coalesce(func.sum(CreditPurchase.amount_eur), 0)).where(
            CreditPurchase.status == PaymentStatus.completed
        )
    )
    total_credit_revenue = float(result.scalar())

    return {
        "total_users": total_users,
        "total_auctions": total_auctions,
        "total_bids": total_bids,
        "active_auctions": active_auctions,
        "completed_auctions": completed_auctions,
        "pending_auctions": pending_auctions,
        "total_credit_revenue": total_credit_revenue,
    }


# ========== ADMIN 2FA (doc §17.3) ==========
# Self-service only - a staff member can only set up/enable/disable TOTP on
# their own account, never another admin's. get_current_staff (not
# get_current_admin) so support-tier accounts can also secure their login.
@admin_router.get("/2fa/status", response_model=TotpStatusResponse)
async def get_2fa_status(current_user: User = Depends(get_current_staff)):
    return TotpStatusResponse(enabled=current_user.totp_enabled)


@admin_router.post("/2fa/setup", response_model=TotpSetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Generate (or regenerate) a TOTP secret. Not yet enabled - the admin
    must add it to an authenticator app and confirm a code via /2fa/verify
    before it's enforced at login."""
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is already enabled. Disable it first to generate a new secret.")
    secret = generate_totp_secret()
    current_user.totp_secret = secret
    await db.commit()
    return TotpSetupResponse(secret=secret, otpauth_url=totp_otpauth_url(secret, current_user.email))


@admin_router.post("/2fa/verify")
async def verify_and_enable_2fa(
    req: TotpCodeRequest,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Confirm the authenticator app is correctly configured, then enable
    2FA enforcement at login."""
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Call /2fa/setup first")
    if not verify_totp(current_user.totp_secret, req.code):
        raise HTTPException(status_code=400, detail="Invalid code")
    current_user.totp_enabled = True
    await db.commit()
    await _log_audit(db, current_user.id, "enable_2fa", "user", current_user.id)
    return {"status": "enabled"}


@admin_router.post("/2fa/disable")
async def disable_2fa(
    req: TotpCodeRequest,
    current_user: User = Depends(get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Requires a currently-valid code (not just the JWT) so a hijacked
    session token alone can't turn off 2FA."""
    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="2FA is not enabled")
    if not verify_totp(current_user.totp_secret, req.code):
        raise HTTPException(status_code=400, detail="Invalid code")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    await db.commit()
    await _log_audit(db, current_user.id, "disable_2fa", "user", current_user.id)
    return {"status": "disabled"}


# ========== NOTIFICATION TEMPLATES (doc §17 admin panel checklist) ==========
def _validate_template_placeholders(text_value: str | None, allowed: list[str]) -> None:
    if not text_value:
        return
    used = {name for _, name, _, _ in string_module.Formatter().parse(text_value) if name}
    unknown = used - set(allowed)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown placeholder(s): {', '.join(sorted(unknown))}. Allowed: {', '.join(allowed) or '(none)'}",
        )


@admin_router.get("/notification-templates", response_model=list[NotificationTemplateResponse])
async def list_notification_templates(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Only the notification types actually wired to read a template at
    send-time are listed - customizing any other type would silently do
    nothing, so it's not offered here (see TEMPLATABLE_NOTIFICATION_TYPES)."""
    result = await db.execute(select(NotificationTemplate))
    existing = {row.type: row for row in result.scalars().all()}
    out = []
    for ntype, placeholders in TEMPLATABLE_NOTIFICATION_TYPES.items():
        row = existing.get(ntype.value)
        out.append(NotificationTemplateResponse(
            type=ntype.value,
            placeholders=placeholders,
            title_en=row.title_en if row else None,
            message_en=row.message_en if row else None,
            title_me=row.title_me if row else None,
            message_me=row.message_me if row else None,
        ))
    return out


@admin_router.put("/notification-templates/{template_type}", response_model=NotificationTemplateResponse)
async def update_notification_template(
    template_type: str,
    req: NotificationTemplateUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        ntype = NotificationType(template_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown notification type")
    if ntype not in TEMPLATABLE_NOTIFICATION_TYPES:
        raise HTTPException(status_code=400, detail="This notification type does not support template customization")
    allowed = TEMPLATABLE_NOTIFICATION_TYPES[ntype]
    for field_value in (req.title_en, req.message_en, req.title_me, req.message_me):
        _validate_template_placeholders(field_value, allowed)

    result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.type == ntype.value))
    row = result.scalars().first()
    if not row:
        row = NotificationTemplate(type=ntype.value)
        db.add(row)
    row.title_en = req.title_en
    row.message_en = req.message_en
    row.title_me = req.title_me
    row.message_me = req.message_me
    await db.commit()

    await _log_audit(db, current_user.id, "update_notification_template", "notification_template", ntype.value)

    return NotificationTemplateResponse(
        type=ntype.value, placeholders=allowed,
        title_en=row.title_en, message_en=row.message_en,
        title_me=row.title_me, message_me=row.message_me,
    )


@admin_router.delete("/notification-templates/{template_type}")
async def reset_notification_template(
    template_type: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revert to the hardcoded default text (delete the override row)."""
    try:
        ntype = NotificationType(template_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown notification type")
    result = await db.execute(select(NotificationTemplate).where(NotificationTemplate.type == ntype.value))
    row = result.scalars().first()
    if row:
        await db.delete(row)
        await db.commit()
        await _log_audit(db, current_user.id, "reset_notification_template", "notification_template", ntype.value)
    return {"status": "reset"}