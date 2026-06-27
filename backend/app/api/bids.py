import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import Auction, AuctionStatus, Bid, User, UserRole, Payment, PaymentStatus
from app.schemas.bid import BidCreateRequest, BidResponse, BidHistoryResponse
from app.api.ws import manager
from app.services.notifications import send_notification, NotificationType

bids_router = APIRouter(prefix="/api/auctions", tags=["bids"])

BID_EXTEND_SECONDS = 300  # 5 minutes

# ========== PLACE BID ==========
@bids_router.post("/{auction_id}/bids", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
async def place_bid(
    auction_id: str,
    req: BidCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a bid on an active auction. Any authenticated user can bid."""
    # Fetch auction
    result = await db.execute(
        select(Auction)
        .where(Auction.id == auction_id)
        .with_for_update()
    )
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
        ip_address=request.client.host if request.client else "",
    )
    db.add(bid)
    await db.commit()
    await db.refresh(bid)

    # Find previous highest bidder (for outbid notification)
    prev_bid_result = await db.execute(
        select(Bid)
        .where(Bid.auction_id == auction_id, Bid.user_id != current_user.id)
        .order_by(desc(Bid.amount))
        .limit(1)
    )
    previous_highest_bidder = prev_bid_result.scalars().first()

    # Notify seller about new bid
    await send_notification(
        db, auction.seller_id,
        NotificationType.bid_received,
        f"New bid on {auction.title}",
        f"Your auction '{auction.title}' received a bid of ${req.amount:.2f}.",
        auction_id=auction_id,
        send_email=True,
    )

    # Notify previous highest bidder that they've been outbid
    if previous_highest_bidder:
        await send_notification(
            db, previous_highest_bidder.user_id,
            NotificationType.outbid,
            f"Outbid on {auction.title}",
            f"Someone placed a higher bid of ${req.amount:.2f} on '{auction.title}'.",
            auction_id=auction_id,
            send_email=True,
        )

    # Broadcast new bid to all connected clients in the auction room
    await manager.broadcast(auction_id, {
        "type": "new_bid",
        "auction_id": auction_id,
        "bid": {
            "id": bid.id,
            "user_id": bid.user_id,
            "amount": bid.amount,
            "created_at": bid.created_at.isoformat() if bid.created_at else None,
        },
        "current_price": auction.current_price,
        "end_time": auction.end_time.isoformat() if auction.end_time else None,
    })

    return BidResponse(
        id=bid.id,
        auction_id=bid.auction_id,
        user_id=bid.user_id,
        amount=bid.amount,
        created_at=bid.created_at,
        user_name=current_user.name,
        auction_title=auction.title,
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

    # Fetch bids with user relationship loaded
    query = (
        select(Bid)
        .options(selectinload(Bid.user))
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
                user_name=b.user.name if b.user else None,
                auction_title=auction.title,
            )
            for b in bids
        ],
        total_count=total_count,
        current_price=auction.current_price,
        auction_status=auction.status.value,
        min_increment=auction.min_increment,
    )


# ========== FINALIZE (determine winner) ==========
@bids_router.post("/{auction_id}/finalize", response_model=dict)
async def finalize_auction(
    auction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Finalize an ended auction: determine the winner (highest bidder)
    and mark the auction as completed. Admins and the seller can call this.
    """
    result = await db.execute(
        select(Auction)
        .where(Auction.id == auction_id)
        .with_for_update()
    )
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    if current_user.role != UserRole.admin and auction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the seller or an admin can finalize this auction")

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

    # Notify winner and create payment record
    if winner_id:
        winner_user = await db.execute(select(User).where(User.id == winner_id))
        winner_user_obj = winner_user.scalars().first()
        if winner_user_obj:
            await send_notification(
                db, winner_id,
                NotificationType.auction_won,
                f"You won: {auction.title}",
                f"Congratulations! You won the auction '{auction.title}' with a bid of ${highest_bid.amount:.2f}.",
                auction_id=auction_id,
                send_email=True,
            )

        # Create pending payment record for winner
        payment = Payment(
            id=str(uuid.uuid4()),
            auction_id=auction_id,
            buyer_id=winner_id,
            amount=highest_bid.amount,
            status=PaymentStatus.pending,
        )
        db.add(payment)

    # Notify seller
    await send_notification(
        db, auction.seller_id,
        NotificationType.auction_completed,
        f"Auction completed: {auction.title}",
        f"Your auction '{auction.title}' has ended. Winner: {winner_id if winner_id else 'No bids'}.",
        auction_id=auction_id,
        send_email=True,
    )

    # Notify other bidders they lost
    if highest_bid:
        other_bidders_result = await db.execute(
            select(Bid.user_id)
            .where(Bid.auction_id == auction_id, Bid.user_id != winner_id)
            .distinct()
        )
        other_bidder_ids = other_bidders_result.scalars().all()
        for loser_id in other_bidder_ids:
            await send_notification(
                db, loser_id,
                NotificationType.auction_lost,
                f"Auction ended: {auction.title}",
                f"The auction '{auction.title}' has ended. Another user won with a bid of ${highest_bid.amount:.2f}.",
                auction_id=auction_id,
                send_email=False,
            )

    # Broadcast auction status change via WebSocket
    await manager.broadcast(auction_id, {
        "type": "auction_status_changed",
        "auction_id": auction_id,
        "status": "completed",
        "winner_user_id": winner_id,
        "winning_bid": highest_bid.amount if highest_bid else None,
    })

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
        .options(selectinload(Bid.auction))
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
            user_name=current_user.name,
            auction_title=b.auction.title if b.auction else None,
        )
        for b in bids
    ]
