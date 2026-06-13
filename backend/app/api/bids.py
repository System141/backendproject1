import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import Auction, AuctionStatus, Bid, User
from app.schemas.bid import BidCreateRequest, BidResponse, BidHistoryResponse

bids_router = APIRouter(prefix="/api/auctions", tags=["bids"])

BID_EXTEND_SECONDS = 300  # 5 minutes

# ========== PLACE BID ==========
@bids_router.post("/{auction_id}/bids", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
async def place_bid(
    auction_id: str,
    req: BidCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a bid on an active auction. Any authenticated user can bid."""
    # Fetch auction
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    # Validate auction is active
    if auction.status != AuctionStatus.active:
        raise HTTPException(status_code=400, detail="Auction is not active")

    # Seller cannot bid on their own auction
    if auction.seller_id == current_user.id:
        raise HTTPException(status_code=403, detail="You cannot bid on your own auction")

    # Validate auction hasn't ended
    now = datetime.now(timezone.utc)
    end_time = auction.end_time
    if end_time.tzinfo is None:
        # Naive datetime, treat as UTC
        end_time = end_time.replace(tzinfo=timezone.utc)
    if now >= end_time:
        raise HTTPException(status_code=400, detail="Auction has ended")

    # Validate minimum increment
    min_allowed = auction.current_price + auction.min_increment
    if req.amount < min_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Bid must be at least {min_allowed:.2f} (current price {auction.current_price:.2f} + minimum increment {auction.min_increment:.2f})",
        )

    # Update auction's current price
    auction.current_price = req.amount

    # Optional: extend end time if bid placed in last N seconds
    time_remaining = (end_time - now).total_seconds()
    if 0 < time_remaining < BID_EXTEND_SECONDS:
        auction.end_time = end_time + timedelta(seconds=BID_EXTEND_SECONDS)

    # Create bid record
    bid_id = str(uuid.uuid4())
    bid = Bid(
        id=bid_id,
        auction_id=auction_id,
        user_id=current_user.id,
        amount=req.amount,
        ip_address="",  # Could capture from request context
    )
    db.add(bid)
    await db.commit()
    await db.refresh(bid)

    return BidResponse(
        id=bid.id,
        auction_id=bid.auction_id,
        user_id=bid.user_id,
        amount=bid.amount,
        created_at=bid.created_at,
    )


# ========== BID HISTORY ==========
@bids_router.get("/{auction_id}/bids", response_model=BidHistoryResponse)
async def get_bid_history(
    auction_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get bid history for an auction, ordered by amount descending."""
    # Verify auction exists
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    # Count total
    count_result = await db.execute(
        select(Bid).where(Bid.auction_id == auction_id)
    )
    total_count = len(count_result.scalars().all())

    # Fetch bids
    query = (
        select(Bid)
        .where(Bid.auction_id == auction_id)
        .order_by(desc(Bid.amount))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    bids = result.scalars().all()

    return BidHistoryResponse(
        bids=[
            BidResponse(
                id=b.id,
                auction_id=b.auction_id,
                user_id=b.user_id,
                amount=b.amount,
                created_at=b.created_at,
            )
            for b in bids
        ],
        total_count=total_count,
    )


# ========== FINALIZE (determine winner) ==========
@bids_router.post("/{auction_id}/finalize", response_model=dict)
async def finalize_auction(
    auction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Finalize an ended auction: determine the winner (highest bidder)
    and mark the auction as completed. Anyone can call this endpoint.
    """
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    # Only active auctions can be finalized
    if auction.status != AuctionStatus.active:
        raise HTTPException(status_code=400, detail=f"Auction is not active (status: {auction.status.value})")

    # Check that end time has passed
    now = datetime.now(timezone.utc)
    end_time = auction.end_time
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    if now < end_time:
        remaining = (end_time - now).total_seconds()
        raise HTTPException(
            status_code=400,
            detail=f"Auction has not ended yet. {remaining:.0f} seconds remaining.",
        )

    # Find the highest bid
    bid_result = await db.execute(
        select(Bid)
        .where(Bid.auction_id == auction_id)
        .order_by(desc(Bid.amount))
        .limit(1)
    )
    highest_bid = bid_result.scalars().first()

    winner_id = highest_bid.user_id if highest_bid else None

    auction.status = AuctionStatus.completed
    auction.winner_user_id = winner_id
    await db.commit()

    return {
        "status": "completed",
        "auction_id": auction_id,
        "winner_user_id": winner_id,
        "winning_bid": highest_bid.amount if highest_bid else None,
        "has_bids": highest_bid is not None,
    }


# ========== MY BIDS ==========
@bids_router.get("/bids/my", response_model=list[BidResponse])
async def my_bids(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's bids across all auctions."""
    result = await db.execute(
        select(Bid)
        .where(Bid.user_id == current_user.id)
        .order_by(desc(Bid.created_at))
    )
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