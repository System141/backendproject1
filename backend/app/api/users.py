from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user, get_current_seller, hash_password, verify_password
from app.models.domain import User, Auction, Bid
from app.schemas.auth import UserResponse
from app.schemas.user import UserUpdateRequest, PasswordChangeRequest

users_router = APIRouter(prefix="/api/users", tags=["users"])


def _user_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        name=u.name,
        email=u.email,
        phone=u.phone,
        city=u.city,
        address=u.address,
        preferred_language=u.preferred_language,
        role=u.role.value if hasattr(u.role, 'value') else str(u.role),
        status=u.status,
        created_at=str(u.created_at) if u.created_at else "",
    )


@users_router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return _user_response(current_user)


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
    if req.city is not None:
        current_user.city = req.city
    if req.address is not None:
        current_user.address = req.address
    if req.preferred_language is not None:
        current_user.preferred_language = req.preferred_language
    if req.marketing_consent is not None:
        current_user.marketing_consent = req.marketing_consent

    await db.commit()
    await db.refresh(current_user)

    return _user_response(current_user)


@users_router.put("/me/password")
async def change_password(
    req: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Doc §10.1 'Security' dashboard tab: self-service password change."""
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(req.new_password)
    await db.commit()
    return {"status": "ok"}


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
    counts = {row[0].value: row[1] for row in counts_result.all()}

    revenue_result = await db.execute(
        select(func.sum(Auction.current_price))
        .where(Auction.seller_id == current_user.id, Auction.status == "ended")
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
        "pending_auctions": counts.get("under_review", 0),
        "active_auctions": counts.get("live", 0) + counts.get("extended", 0),
        "completed_auctions": counts.get("ended", 0),
        "total_revenue": total_revenue,
        "total_bids_received": total_bids,
    }