"""Watchlist API (doc §10.5): follow/unfollow auctions, synced across devices."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import Watchlist, Auction, User
from app.schemas.auction import AuctionResponse
from app.services.auctions import build_auction_response

watchlist_router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@watchlist_router.get("", response_model=list[AuctionResponse])
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's watched auctions."""
    result = await db.execute(
        select(Auction)
        .join(Watchlist, Watchlist.auction_id == Auction.id)
        .options(selectinload(Auction.images), selectinload(Auction.seller))
        .where(Watchlist.user_id == current_user.id)
    )
    return [build_auction_response(a) for a in result.scalars().all()]


@watchlist_router.post("/{auction_id}", status_code=204)
async def add_to_watchlist(
    auction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an auction to the watchlist. Idempotent - calling twice is a no-op."""
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Auction not found")

    db.add(Watchlist(id=str(uuid.uuid4()), user_id=current_user.id, auction_id=auction_id))
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()  # already watchlisted - fine, no-op


@watchlist_router.delete("/{auction_id}", status_code=204)
async def remove_from_watchlist(
    auction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an auction from the watchlist. Idempotent."""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == current_user.id,
            Watchlist.auction_id == auction_id,
        )
    )
    entry = result.scalars().first()
    if entry:
        await db.delete(entry)
        await db.commit()
