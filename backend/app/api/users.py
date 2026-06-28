from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user, get_current_seller
from app.models.domain import User, Auction, Bid
from app.schemas.auth import UserResponse
from app.schemas.user import UserUpdateRequest

users_router = APIRouter(prefix="/api/users", tags=["users"])


@users_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        status=current_user.status,
        created_at=str(current_user.created_at) if current_user.created_at else "",
    )


@users_router.put("/me", response_model=UserResponse)
async def update_me(
    req: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if req.name is not None:
        current_user.name = req.name
    if req.phone is not None:
        current_user.phone = req.phone
    if req.marketing_consent is not None:
        current_user.marketing_consent = req.marketing_consent

    await db.commit()
    await db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        status=current_user.status,
        created_at=str(current_user.created_at) if current_user.created_at else "",
    )


@users_router.get("/me/seller-stats")
async def seller_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Corporate/seller performance dashboard stats."""
    counts_result = await db.execute(
        select(Auction.status, func.count(Auction.id))
        .where(Auction.seller_id == current_user.id)
        .group_by(Auction.status)
    )
    counts = {str(row[0]): row[1] for row in counts_result.all()}

    revenue_result = await db.execute(
        select(func.sum(Auction.current_price))
        .where(Auction.seller_id == current_user.id, Auction.status == "completed")
    )
    total_revenue = float(revenue_result.scalar() or 0)

    bids_result = await db.execute(
        select(func.count(Bid.id))
        .join(Auction, Bid.auction_id == Auction.id)
        .where(Auction.seller_id == current_user.id)
    )
    total_bids = int(bids_result.scalar() or 0)

    return {
        "total_auctions": sum(counts.values()),
        "pending_auctions": counts.get("pending_approval", 0),
        "active_auctions": counts.get("active", 0),
        "completed_auctions": counts.get("completed", 0),
        "total_revenue": total_revenue,
        "total_bids_received": total_bids,
    }