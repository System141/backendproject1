import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, get_current_seller, get_current_admin, get_current_user_optional
from app.models.domain import (
    Auction, AuctionStatus, AuctionImage, AuctionParticipant, Bid, Category, User, UserRole, NotificationType,
    SellerProfile, SellerVerificationStatus, TermsAcceptance, _utcnow, to_naive_utc,
)
from app.services.notifications import send_notification
from app.services.auctions import (
    build_auction_response, build_auction_image_response, visible_auction_images,
    generate_lot_code, looks_like_direct_contact, get_or_create_seller_declaration,
)
from app.schemas.auction import (
    AuctionCreateRequest,
    AuctionUpdateRequest,
    AuctionResponse,
    AuctionDetailResponse,
    AuctionImageResponse,
    AuctionStatusUpdate,
    CategoryBrief,
    ContactInfoResponse,
)
from app.schemas.bid import JoinedAuctionResponse
from app.schemas.credit import ReasonRequest

auctions_router = APIRouter(prefix="/api/auctions", tags=["auctions"])


# ---------- Helper: fetch auction with seller check ----------
async def _get_auction_or_404(db: AsyncSession, auction_id: str) -> Auction:
    result = await db.execute(
        select(Auction)
        .options(selectinload(Auction.images))
        .options(selectinload(Auction.seller).selectinload(User.seller_profile))
        .where(Auction.id == auction_id)
    )
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction


def _build_auction_response(auction: Auction) -> AuctionResponse:
    """Build AuctionResponse using the shared service function."""
    return build_auction_response(auction)


# ========== CREATE ==========
@auctions_router.post("", response_model=AuctionResponse, status_code=status.HTTP_201_CREATED)
async def create_auction(
    req: AuctionCreateRequest,
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Create a new auction listing. Requires a verified SellerProfile (doc
    §11.1/§11.5) - self-declared seller/corporate_seller role alone isn't
    enough to publish."""
    if not req.declaration_accepted:
        raise HTTPException(status_code=400, detail="You must confirm the seller declaration to submit a listing")

    profile_result = await db.execute(select(SellerProfile).where(SellerProfile.user_id == current_user.id))
    profile = profile_result.scalars().first()
    if not profile or profile.verification_status != SellerVerificationStatus.verified:
        raise HTTPException(status_code=403, detail="Apply as a seller and get verified before creating listings")

    # Validate category exists
    cat_result = await db.execute(select(Category).where(Category.id == req.category_id))
    category = cat_result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Normalize to naive UTC before comparing/storing - asyncpg rejects
    # tz-aware datetimes bound to the DateTime (TIMESTAMP WITHOUT TIME ZONE) column
    end_time = to_naive_utc(req.end_time)
    now = _utcnow()

    # Validate end_time is in the future
    if end_time <= now:
        raise HTTPException(status_code=400, detail="End time must be in the future")

    listing_fee = float(os.getenv("LISTING_FEE_CREDITS", "10"))
    if (current_user.credits_balance or 0.0) < listing_fee:
        raise HTTPException(status_code=402, detail="Insufficient credits to post a listing")
    current_user.credits_balance = (current_user.credits_balance or 0.0) - listing_fee

    auction_id = str(uuid.uuid4())
    lot_code = await generate_lot_code(db, category)

    auction = Auction(
        id=auction_id,
        seller_id=current_user.id,
        category_id=req.category_id,
        title=req.title,
        description=req.description,
        start_price=req.start_price,
        current_price=req.start_price,  # initial = start_price
        min_increment=req.min_increment,
        start_time=now,
        end_time=end_time,
        status=AuctionStatus.under_review,
        brand=req.brand,
        model=req.model,
        year=req.year,
        mileage=req.mileage,
        fuel_type=req.fuel_type,
        transmission=req.transmission,
        damage_status=req.damage_status,
        defect_exterior=req.defect_exterior,
        defect_interior=req.defect_interior,
        defect_mechanical=req.defect_mechanical,
        defect_tyres=req.defect_tyres,
        defect_missing_parts=req.defect_missing_parts,
        equipment_brand=req.equipment_brand,
        serial_number=req.serial_number,
        condition=req.condition,
        location=req.location,
        operating_hours=req.operating_hours,
        engine_power=req.engine_power,
        operating_weight=req.operating_weight,
        service_history=req.service_history,
        inspection_availability=req.inspection_availability,
        dimensions=req.dimensions,
        included_items=req.included_items,
        quantity=req.quantity,
        listing_fee=listing_fee,
        lot_code=lot_code,
        contact_flagged=looks_like_direct_contact(req.title, req.description),
    )
    db.add(auction)
    declaration = await get_or_create_seller_declaration(db)
    db.add(TermsAcceptance(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        document_type="seller_listing_declaration",
        version=declaration.version,
    ))

    await db.commit()
    auction = await _get_auction_or_404(db, auction_id)

    return _build_auction_response(auction)


# ========== LIST (public) ==========
@auctions_router.get("", response_model=list[AuctionResponse])
async def list_auctions(
    response: Response,
    category_id: int | None = Query(None, description="Filter by category"),
    status: str | None = Query(None, description="Filter by status (draft, under_review, upcoming, live, extended, ended, cancelled)"),
    search: str | None = Query(None, min_length=2, description="Search across Lot ID, title, description, brand, model, city (doc §13.1)"),
    city: str | None = Query(None, description="Filter by city/location"),
    seller_id: str | None = Query(None, description="Filter by seller"),
    seller_type: str | None = Query(None, description="Filter by seller type (dealer, rent-a-car, insurer, construction, individual, ...) (doc §4.1)"),
    winner_user_id: str | None = Query(None, description="Filter by winner"),
    sort_by: str = Query("created_at", pattern=r"^(created_at|end_time|start_price|current_price)$"),
    sort_dir: str = Query("desc", pattern=r"^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List auctions with optional filters. Public endpoint. Total matching
    count (pre-pagination) is returned in the X-Total-Count header for
    frontend pagination/load-more (doc §4.4)."""
    query = select(Auction).options(selectinload(Auction.images), selectinload(Auction.seller).selectinload(User.seller_profile))

    if category_id:
        query = query.where(Auction.category_id == category_id)
    if status:
        query = query.where(Auction.status == AuctionStatus(status))
    else:
        # Default: only show publicly-relevant states (never draft/under_review/cancelled)
        query = query.where(Auction.status.in_(
            [AuctionStatus.upcoming, AuctionStatus.live, AuctionStatus.extended, AuctionStatus.ended]
        ))
    if search:
        pattern = f"%{search}%"
        query = query.where(
            Auction.title.ilike(pattern)
            | Auction.description.ilike(pattern)
            | Auction.lot_code.ilike(pattern)
            | Auction.brand.ilike(pattern)
            | Auction.model.ilike(pattern)
            | Auction.equipment_brand.ilike(pattern)
            | Auction.location.ilike(pattern)
        )
    if city:
        query = query.where(Auction.location.ilike(f"%{city}%"))
    if seller_id:
        query = query.where(Auction.seller_id == seller_id)
    if seller_type:
        query = query.join(User, User.id == Auction.seller_id).join(
            SellerProfile, SellerProfile.user_id == User.id
        ).where(SellerProfile.seller_type.ilike(f"%{seller_type}%"))
    if winner_user_id:
        query = query.where(Auction.winner_user_id == winner_user_id)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    response.headers["X-Total-Count"] = str(count_result.scalar())

    # Sorting
    sort_col = getattr(Auction, sort_by)
    order_fn = desc if sort_dir == "desc" else asc
    query = query.order_by(order_fn(sort_col))

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    auctions = result.scalars().all()

    return [_build_auction_response(a) for a in auctions]


# ========== AUTOCOMPLETE (public, doc §13.2) ==========
@auctions_router.get("/autocomplete", response_model=list[str])
async def autocomplete_auctions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=25),
    db: AsyncSession = Depends(get_db),
):
    """Lot ID / make / model / city suggestions for the search box (doc
    §13.2). Client is expected to debounce; min_length=2 enforces the
    "minimum karakter sayısı" side of that requirement server-side too.

    # ponytail: fetches a flat 100-row window then dedupes in Python, so a
    # match ranked past row 100 (e.g. by location) can be missed once the
    # table holds 1000+ listings (§4.4 scale target). Upgrade path: UNION of
    # per-column DISTINCT queries if that ceiling is hit."""
    pattern = f"%{q}%"
    result = await db.execute(
        select(Auction.lot_code, Auction.brand, Auction.model, Auction.equipment_brand, Auction.location)
        .where(
            Auction.status.in_([AuctionStatus.upcoming, AuctionStatus.live, AuctionStatus.extended, AuctionStatus.ended]),
            Auction.lot_code.ilike(pattern)
            | Auction.brand.ilike(pattern)
            | Auction.model.ilike(pattern)
            | Auction.equipment_brand.ilike(pattern)
            | Auction.location.ilike(pattern),
        )
        .limit(100)  # over-fetch raw rows, dedupe below, then cap to `limit`
    )
    suggestions: list[str] = []
    seen = set()
    for lot_code, brand, model, equipment_brand, location in result.all():
        for value in (lot_code, brand, model, equipment_brand, location):
            if value and q.lower() in value.lower() and value not in seen:
                seen.add(value)
                suggestions.append(value)
    return suggestions[:limit]


# ========== MY AUCTIONS (seller) ==========
@auctions_router.get("/my", response_model=list[AuctionResponse])
async def my_auctions(
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """List current user's own auctions. Seller only."""
    result = await db.execute(
        select(Auction)
        .options(selectinload(Auction.images), selectinload(Auction.seller).selectinload(User.seller_profile))
        .where(Auction.seller_id == current_user.id)
        .order_by(desc(Auction.created_at))
    )
    auctions = result.scalars().all()
    return [_build_auction_response(a) for a in auctions]


@auctions_router.get("/joined", response_model=list[JoinedAuctionResponse])
async def joined_auctions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Doc §10.4 Joined Auctions: auctions the current user spent participation
    credits to join, with join date, credits spent, auction status and this
    user's bid standing. Must be registered before the /{auction_id} route
    below - Starlette matches path routes in registration order, so a literal
    "/joined" would otherwise be swallowed as auction_id="joined"."""
    result = await db.execute(
        select(AuctionParticipant)
        .options(selectinload(AuctionParticipant.auction))
        .where(AuctionParticipant.user_id == current_user.id)
        .order_by(desc(AuctionParticipant.joined_at))
    )
    participants = result.scalars().all()

    responses = []
    for p in participants:
        auction = p.auction
        my_bid_status = "no_bid"
        if auction:
            highest_result = await db.execute(
                select(Bid)
                .where(Bid.auction_id == auction.id, Bid.invalidated == False)  # noqa: E712
                .order_by(desc(Bid.amount), asc(Bid.created_at))
                .limit(1)
            )
            highest_bid = highest_result.scalars().first()
            if highest_bid:
                my_bid_status = "highest" if highest_bid.user_id == current_user.id else "outbid"
        responses.append(JoinedAuctionResponse(
            auction_id=p.auction_id,
            auction_title=auction.title if auction else "",
            auction_status=auction.status.value if auction else "",
            credits_spent=p.credits_spent,
            joined_at=p.joined_at,
            my_bid_status=my_bid_status,
        ))
    return responses


# ========== DETAIL (public) ==========
@auctions_router.get("/{auction_id}", response_model=AuctionDetailResponse)
async def get_auction(
    auction_id: str,
    db: AsyncSession = Depends(get_db),
    viewer: Optional[dict] = Depends(get_current_user_optional),
):
    """Get auction detail with images and category info. Public - but doc
    §6.2's private documents are only included for the auction's own seller
    or staff/admin, never for anyone else (including anonymous visitors)."""
    auction = await _get_auction_or_404(db, auction_id)

    # Fetch category
    category = None
    cat_result = await db.execute(select(Category).where(Category.id == auction.category_id))
    cat_obj = cat_result.scalars().first()
    if cat_obj:
        category = CategoryBrief(id=cat_obj.id, name=cat_obj.name, slug=cat_obj.slug)

    viewer_user_id = viewer.get("sub") if viewer else None
    viewer_is_staff = viewer is not None and viewer.get("role") in ("admin", "super_admin", "support")
    images = [
        build_auction_image_response(img)
        for img in visible_auction_images(auction, viewer_user_id, viewer_is_staff)
    ]

    base = _build_auction_response(auction)
    return AuctionDetailResponse(
        **base.model_dump(),
        images=images,
        category=category,
    )


# ========== UPDATE (seller, only if pending) ==========
@auctions_router.put("/{auction_id}", response_model=AuctionResponse)
async def update_auction(
    auction_id: str,
    req: AuctionUpdateRequest,
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Update an auction. Only the owner seller can update, and only while
    under_review or draft (draft = admin requested changes, doc §11.5)."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own auctions")
    if auction.status not in (AuctionStatus.under_review, AuctionStatus.draft):
        raise HTTPException(status_code=400, detail="Can only update auctions under review or with requested changes")

    # Update only provided fields
    update_data = req.model_dump(exclude_unset=True)
    if "end_time" in update_data:
        update_data["end_time"] = to_naive_utc(update_data["end_time"])
    for field, value in update_data.items():
        setattr(auction, field, value)
    auction.contact_flagged = looks_like_direct_contact(auction.title, auction.description)

    await db.commit()
    auction = await _get_auction_or_404(db, auction_id)

    return _build_auction_response(auction)


# ========== SUBMIT (seller, resubmit after changes requested) ==========
@auctions_router.post("/{auction_id}/submit", response_model=AuctionResponse)
async def submit_auction(
    auction_id: str,
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Resubmit a draft (changes-requested) auction for review (doc §11.5)."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only submit your own auctions")
    if auction.status != AuctionStatus.draft:
        raise HTTPException(status_code=400, detail="Only draft auctions can be submitted")

    auction.status = AuctionStatus.under_review
    await db.commit()
    auction = await _get_auction_or_404(db, auction_id)
    return _build_auction_response(auction)


# ========== DELETE (seller, only if pending) ==========
@auctions_router.delete("/{auction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_auction(
    auction_id: str,
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Delete an auction. Only the owner seller, and only while under review or draft."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own auctions")
    if auction.status not in (AuctionStatus.under_review, AuctionStatus.draft):
        raise HTTPException(status_code=400, detail="Can only delete auctions under review or with requested changes")

    await db.delete(auction)
    await db.commit()


# ========== APPROVE (admin) ==========
@auctions_router.post("/{auction_id}/approve", response_model=AuctionResponse)
async def approve_auction(
    auction_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve an auction (admin only). Sets status to upcoming (start_time in the
    future) or live (start_time already reached)."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.status != AuctionStatus.under_review:
        raise HTTPException(status_code=400, detail="Only auctions under review can be approved")

    auction.status = AuctionStatus.upcoming if auction.start_time > _utcnow() else AuctionStatus.live
    await db.commit()
    auction = await _get_auction_or_404(db, auction_id)

    # Notify seller
    await send_notification(
        db, auction.seller_id,
        NotificationType.auction_approved,
        f"Auction approved: {auction.title}",
        f"Your auction '{auction.title}' has been approved and is now live.",
        auction_id=auction_id,
        send_email=True,
        title_me=f"Aukcija odobrena: {auction.title}",
        message_me=f"Vaša aukcija '{auction.title}' je odobrena i sada je aktivna.",
        template_vars={"auction_title": auction.title},
    )

    return _build_auction_response(auction)


# ========== REQUEST CHANGES (admin) ==========
@auctions_router.post("/{auction_id}/request-changes", response_model=AuctionResponse)
async def request_auction_changes(
    auction_id: str,
    req: ReasonRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Send an under-review auction back to the seller for edits (doc §11.5).
    Sets status to draft (seller-editable) with the admin's feedback in
    review_notes; the seller resubmits via POST /{id}/submit.
    """
    auction = await _get_auction_or_404(db, auction_id)

    if auction.status != AuctionStatus.under_review:
        raise HTTPException(status_code=400, detail="Only auctions under review can have changes requested")

    auction.status = AuctionStatus.draft
    auction.review_notes = req.reason
    await db.commit()
    auction = await _get_auction_or_404(db, auction_id)

    await send_notification(
        db, auction.seller_id,
        NotificationType.listing_changes_requested,
        f"Changes requested: {auction.title}",
        f"Please update your listing '{auction.title}': {req.reason}",
        auction_id=auction_id,
        send_email=True,
        title_me=f"Zatražene izmjene: {auction.title}",
        message_me=f"Molimo ažurirajte svoj oglas '{auction.title}': {req.reason}",
        template_vars={"auction_title": auction.title, "reason": req.reason},
    )

    return _build_auction_response(auction)


# ========== CONTACT UNLOCK (post-close, doc §12.5/§5.11 - AC-11/AC-12) ==========
@auctions_router.get("/{auction_id}/contact", response_model=ContactInfoResponse)
async def get_auction_contact(
    auction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reveal the other party's contact info once the auction has ended.
    Never available while an auction is live/extended - the seller
    is only shown as "Verified Seller" (§5.11) until close, and this
    is the sole place seller/winner phone or email is ever returned.
    """
    auction = await _get_auction_or_404(db, auction_id)

    if auction.status != AuctionStatus.ended:
        raise HTTPException(status_code=400, detail="Contact info unlocks only after the auction ends")
    if not auction.winner_user_id:
        raise HTTPException(status_code=404, detail="This auction ended with no winning bidder")

    if current_user.id == auction.winner_user_id:
        target_id, role = auction.seller_id, "seller"
    elif current_user.id == auction.seller_id:
        target_id, role = auction.winner_user_id, "winner"
    else:
        raise HTTPException(status_code=403, detail="Only the seller or the highest bidder can view this")

    target_result = await db.execute(select(User).where(User.id == target_id))
    target = target_result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="Contact not found")

    return ContactInfoResponse(role=role, name=target.name, email=target.email, phone=target.phone)


# ========== REJECT (admin) ==========
@auctions_router.post("/{auction_id}/reject", response_model=AuctionResponse)
async def reject_auction(
    auction_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reject an auction (admin only). Sets status to cancelled."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.status != AuctionStatus.under_review:
        raise HTTPException(status_code=400, detail="Only auctions under review can be rejected")

    auction.status = AuctionStatus.cancelled
    await db.commit()
    auction = await _get_auction_or_404(db, auction_id)

    # Notify seller
    await send_notification(
        db, auction.seller_id,
        NotificationType.auction_rejected,
        f"Auction rejected: {auction.title}",
        f"Your auction '{auction.title}' has been rejected by the admin.",
        auction_id=auction_id,
        send_email=True,
        title_me=f"Aukcija odbijena: {auction.title}",
        message_me=f"Vaša aukcija '{auction.title}' je odbijena od strane administratora.",
        template_vars={"auction_title": auction.title},
    )

    return _build_auction_response(auction)
