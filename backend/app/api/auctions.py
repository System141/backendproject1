import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, get_current_seller, get_current_admin
from app.models.domain import Auction, AuctionStatus, AuctionImage, Category, User, UserRole, NotificationType
from app.services.notifications import send_notification
from app.schemas.auction import (
    AuctionCreateRequest,
    AuctionUpdateRequest,
    AuctionResponse,
    AuctionDetailResponse,
    AuctionImageResponse,
    AuctionStatusUpdate,
    CategoryBrief,
)

auctions_router = APIRouter(prefix="/api/auctions", tags=["auctions"])


# ---------- Helper: fetch auction with seller check ----------
async def _get_auction_or_404(db: AsyncSession, auction_id: str) -> Auction:
    result = await db.execute(
        select(Auction)
        .options(selectinload(Auction.images))
        .options(selectinload(Auction.seller))
        .where(Auction.id == auction_id)
    )
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction


def _build_auction_response(auction: Auction) -> AuctionResponse:
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


# ========== CREATE ==========
@auctions_router.post("", response_model=AuctionResponse, status_code=status.HTTP_201_CREATED)
async def create_auction(
    req: AuctionCreateRequest,
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Create a new auction listing (seller / corporate_seller only)."""
    # Validate category exists
    cat_result = await db.execute(select(Category).where(Category.id == req.category_id))
    category = cat_result.scalars().first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Validate end_time is in the future
    if req.end_time <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="End time must be in the future")

    auction_id = str(uuid.uuid4())
    now = datetime.utcnow()

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
        end_time=req.end_time,
        status=AuctionStatus.pending_approval,
        brand=req.brand,
        model=req.model,
        year=req.year,
        mileage=req.mileage,
        fuel_type=req.fuel_type,
        transmission=req.transmission,
        damage_status=req.damage_status,
        equipment_brand=req.equipment_brand,
        serial_number=req.serial_number,
        condition=req.condition,
        location=req.location,
    )
    db.add(auction)
    await db.commit()
    await db.refresh(auction)

    return _build_auction_response(auction)


# ========== LIST (public) ==========
@auctions_router.get("", response_model=list[AuctionResponse])
async def list_auctions(
    category_id: int | None = Query(None, description="Filter by category"),
    status: str | None = Query(None, description="Filter by status (active, pending_approval, completed, cancelled)"),
    search: str | None = Query(None, min_length=2, description="Search in title/description"),
    seller_id: str | None = Query(None, description="Filter by seller"),
    winner_user_id: str | None = Query(None, description="Filter by winner"),
    sort_by: str = Query("created_at", regex=r"^(created_at|end_time|start_price|current_price)$"),
    sort_dir: str = Query("desc", regex=r"^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List auctions with optional filters. Public endpoint."""
    query = select(Auction).options(selectinload(Auction.images))

    if category_id:
        query = query.where(Auction.category_id == category_id)
    if status:
        query = query.where(Auction.status == AuctionStatus(status))
    else:
        # Default: only show active + completed publicly
        query = query.where(Auction.status.in_([AuctionStatus.active, AuctionStatus.completed]))
    if search:
        pattern = f"%{search}%"
        query = query.where(
            Auction.title.ilike(pattern) | Auction.description.ilike(pattern)
        )
    if seller_id:
        query = query.where(Auction.seller_id == seller_id)
    if winner_user_id:
        query = query.where(Auction.winner_user_id == winner_user_id)

    # Sorting
    sort_col = getattr(Auction, sort_by)
    order_fn = desc if sort_dir == "desc" else asc
    query = query.order_by(order_fn(sort_col))

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    auctions = result.scalars().all()

    return [_build_auction_response(a) for a in auctions]


# ========== MY AUCTIONS (seller) ==========
@auctions_router.get("/my", response_model=list[AuctionResponse])
async def my_auctions(
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """List current user's own auctions. Seller only."""
    result = await db.execute(
        select(Auction)
        .options(selectinload(Auction.images))
        .where(Auction.seller_id == current_user.id)
        .order_by(desc(Auction.created_at))
    )
    auctions = result.scalars().all()
    return [_build_auction_response(a) for a in auctions]


# ========== DETAIL (public) ==========
@auctions_router.get("/{auction_id}", response_model=AuctionDetailResponse)
async def get_auction(
    auction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get auction detail with images and category info. Public."""
    auction = await _get_auction_or_404(db, auction_id)

    # Fetch category
    category = None
    cat_result = await db.execute(select(Category).where(Category.id == auction.category_id))
    cat_obj = cat_result.scalars().first()
    if cat_obj:
        category = CategoryBrief(id=cat_obj.id, name=cat_obj.name, slug=cat_obj.slug)

    # Build images
    images = [
        AuctionImageResponse(id=img.id, image_url=img.image_url, sort_order=img.sort_order)
        for img in (auction.images or [])
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
    """Update an auction. Only the owner seller can update, and only while pending."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own auctions")
    if auction.status != AuctionStatus.pending_approval:
        raise HTTPException(status_code=400, detail="Can only update pending auctions")

    # Update only provided fields
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(auction, field, value)

    await db.commit()
    await db.refresh(auction)

    return _build_auction_response(auction)


# ========== DELETE (seller, only if pending) ==========
@auctions_router.delete("/{auction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_auction(
    auction_id: str,
    current_user: User = Depends(get_current_seller),
    db: AsyncSession = Depends(get_db),
):
    """Delete an auction. Only the owner seller, and only while pending."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own auctions")
    if auction.status != AuctionStatus.pending_approval:
        raise HTTPException(status_code=400, detail="Can only delete pending auctions")

    await db.delete(auction)
    await db.commit()


# ========== APPROVE (admin) ==========
@auctions_router.post("/{auction_id}/approve", response_model=AuctionResponse)
async def approve_auction(
    auction_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve an auction (admin only). Sets status to active."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.status != AuctionStatus.pending_approval:
        raise HTTPException(status_code=400, detail="Only pending auctions can be approved")

    auction.status = AuctionStatus.active
    await db.commit()
    await db.refresh(auction)

    # Notify seller
    await send_notification(
        db, auction.seller_id,
        NotificationType.auction_approved,
        f"Auction approved: {auction.title}",
        f"Your auction '{auction.title}' has been approved and is now live.",
        auction_id=auction_id,
        send_email=True,
    )

    return _build_auction_response(auction)


# ========== REJECT (admin) ==========
@auctions_router.post("/{auction_id}/reject", response_model=AuctionResponse)
async def reject_auction(
    auction_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reject an auction (admin only). Sets status to cancelled."""
    auction = await _get_auction_or_404(db, auction_id)

    if auction.status != AuctionStatus.pending_approval:
        raise HTTPException(status_code=400, detail="Only pending auctions can be rejected")

    auction.status = AuctionStatus.cancelled
    await db.commit()
    await db.refresh(auction)

    # Notify seller
    await send_notification(
        db, auction.seller_id,
        NotificationType.auction_rejected,
        f"Auction rejected: {auction.title}",
        f"Your auction '{auction.title}' has been rejected by the admin.",
        auction_id=auction_id,
        send_email=True,
    )

    return _build_auction_response(auction)
