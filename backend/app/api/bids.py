import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import Auction, AuctionStatus, BIDDABLE_STATUSES, AuctionParticipant, Bid, CreditLedgerType, User, UserRole, to_naive_utc
from app.schemas.bid import BidCreateRequest, BidResponse, BidHistoryResponse, JoinAuctionResponse
from app.api.ws import manager
from app.api.auth import limiter
from app.services.notifications import send_notification, NotificationType
from app.services.auctions import finalize_auction, get_bid_increment, get_or_create_settings, anonymize_bidder
from app.services.credits import apply_ledger_entry

bids_router = APIRouter(prefix="/api/auctions", tags=["bids"])


# ========== JOIN AUCTION ==========
@bids_router.post("/{auction_id}/join", response_model=JoinAuctionResponse)
@limiter.limit("20/minute")
async def join_auction(
    request: Request,
    auction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Spend participation credits once to join an auction. Bidding is only
    allowed after joining. Calling this again after already joining is a
    no-op (returns the existing membership, no second charge) so a retried
    request can never double-spend.
    """
    # Capture the plain id up front: db.rollback() (in the race-recovery path
    # below) expires every ORM attribute on objects in this session, and
    # touching current_user.id afterwards without an await would raise
    # MissingGreenlet under async SQLAlchemy (Postgres surfaces this;
    # SQLite/aiosqlite happens to tolerate it).
    user_id = current_user.id

    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status not in BIDDABLE_STATUSES:
        raise HTTPException(status_code=400, detail="Auction is not open for joining")
    if auction.seller_id == user_id:
        raise HTTPException(status_code=403, detail="Sellers cannot join their own auction")

    existing_result = await db.execute(
        select(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction_id,
            AuctionParticipant.user_id == user_id,
        )
    )
    participant = existing_result.scalars().first()
    if participant:
        return JoinAuctionResponse(
            auction_id=auction_id,
            user_id=user_id,
            credits_spent=participant.credits_spent,
            joined_at=participant.joined_at,
            already_joined=True,
        )

    settings = await get_or_create_settings(db)
    cost = auction.participation_credit_cost
    if cost is None:
        cost = settings.default_participation_credit_cost

    # 402 (insufficient balance) is raised here before any row is written.
    await apply_ledger_entry(db, current_user, -cost, CreditLedgerType.join_spend, reference=auction_id)

    participant = AuctionParticipant(
        id=str(uuid.uuid4()),
        auction_id=auction_id,
        user_id=user_id,
        credits_spent=cost,
    )
    db.add(participant)
    try:
        await db.commit()
    except IntegrityError:
        # Lost a race against a concurrent join by the same user: the credit
        # spend above rolls back with the transaction, so no double charge.
        await db.rollback()
        existing_result = await db.execute(
            select(AuctionParticipant).where(
                AuctionParticipant.auction_id == auction_id,
                AuctionParticipant.user_id == user_id,
            )
        )
        participant = existing_result.scalars().first()
        return JoinAuctionResponse(
            auction_id=auction_id,
            user_id=user_id,
            credits_spent=participant.credits_spent,
            joined_at=participant.joined_at,
            already_joined=True,
        )

    await db.refresh(participant)

    await send_notification(
        db, user_id,
        NotificationType.auction_joined,
        f"You joined: {auction.title}",
        f"You spent {cost:.2f} credits to join '{auction.title}'. You can now place bids.",
        auction_id=auction_id,
        send_email=False,
        event_key=f"auction_joined:{auction_id}:{user_id}",
        title_me=f"Pridružili ste se: {auction.title}",
        message_me=f"Potrošili ste {cost:.2f} kredita da se pridružite '{auction.title}'. Sada možete licitirati.",
    )

    return JoinAuctionResponse(
        auction_id=auction_id,
        user_id=user_id,
        credits_spent=participant.credits_spent,
        joined_at=participant.joined_at,
        already_joined=False,
    )


# ========== PLACE BID ==========
@bids_router.post("/{auction_id}/bids", response_model=BidResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def place_bid(
    auction_id: str,
    req: BidCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a bid on an active auction. Requires having joined the auction first."""
    # Idempotency: a retried request with the same key returns the original bid.
    if req.idempotency_key:
        existing_result = await db.execute(
            select(Bid).where(
                Bid.idempotency_key == req.idempotency_key,
                Bid.user_id == current_user.id,
            )
        )
        existing_bid = existing_result.scalars().first()
        if existing_bid:
            return BidResponse(
                id=existing_bid.id,
                auction_id=existing_bid.auction_id,
                user_id=existing_bid.user_id,
                amount=existing_bid.amount,
                created_at=existing_bid.created_at,
                user_name=current_user.name,
            )

    # Fetch auction
    result = await db.execute(
        select(Auction)
        .where(Auction.id == auction_id)
        .with_for_update()
    )
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    # Validate auction is open for bidding
    if auction.status not in BIDDABLE_STATUSES:
        raise HTTPException(status_code=400, detail="Auction is not open for bidding")

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

    # Must have joined (spent participation credits) before bidding
    participant_result = await db.execute(
        select(AuctionParticipant).where(
            AuctionParticipant.auction_id == auction_id,
            AuctionParticipant.user_id == current_user.id,
        )
    )
    if not participant_result.scalars().first():
        raise HTTPException(status_code=403, detail="Join the auction before bidding")

    # Validate minimum increment (admin-configurable, falls back to the
    # auction's own min_increment until BidIncrementRule ranges exist)
    increment = await get_bid_increment(db, auction.current_price, auction.min_increment)
    min_allowed = auction.current_price + increment
    if req.amount < min_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Bid must be at least {min_allowed:.2f} (current price {auction.current_price:.2f} + minimum increment {increment:.2f})",
        )

    # Update auction's current price and the increment shown for the *next* bid
    auction.current_price = req.amount
    auction.min_increment = await get_bid_increment(db, req.amount, auction.min_increment)

    # Anti-sniping: extend the deadline if a valid bid lands within the configured window
    settings = await get_or_create_settings(db)
    time_remaining = (end_time - now).total_seconds()
    deadline_extended = 0 < time_remaining < settings.anti_sniping_window_seconds
    if deadline_extended:
        auction.end_time = to_naive_utc(end_time + timedelta(seconds=settings.anti_sniping_extension_seconds))
        auction.status = AuctionStatus.extended

    # Create bid record
    bid_id = str(uuid.uuid4())
    bid = Bid(
        id=bid_id,
        auction_id=auction_id,
        user_id=current_user.id,
        amount=req.amount,
        ip_address=request.client.host if request.client else "",
        idempotency_key=req.idempotency_key,
    )
    db.add(bid)
    await db.commit()
    await db.refresh(bid)

    # Find previous highest bidder (for outbid notification)
    prev_bid_result = await db.execute(
        select(Bid)
        .where(Bid.auction_id == auction_id, Bid.user_id != current_user.id, Bid.invalidated == False)  # noqa: E712
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
        title_me=f"Nova ponuda na {auction.title}",
        message_me=f"Vaša aukcija '{auction.title}' je dobila ponudu od ${req.amount:.2f}.",
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
            title_me=f"Nadmašena ponuda na {auction.title}",
            message_me=f"Neko je postavio veću ponudu od ${req.amount:.2f} na '{auction.title}'.",
        )

    # Notify seller the deadline moved (anti-sniping, doc §16.1) - keyed on
    # this specific bid so a retried request can't double-notify.
    if deadline_extended:
        await send_notification(
            db, auction.seller_id,
            NotificationType.auction_extended,
            f"Deadline extended: {auction.title}",
            f"A last-minute bid pushed the end time of '{auction.title}' back to {auction.end_time.isoformat()}.",
            auction_id=auction_id,
            send_email=False,
            title_me=f"Rok produžen: {auction.title}",
            message_me=f"Ponuda u posljednjem trenutku je pomjerila kraj aukcije '{auction.title}' na {auction.end_time.isoformat()}.",
            event_key=f"auction_extended:{bid_id}",
        )

    # Broadcast new bid to all connected clients in the auction room
    await manager.broadcast(auction_id, {
        "type": "new_bid",
        "auction_id": auction_id,
        "bid": {
            "id": bid.id,
            "user_name": anonymize_bidder(auction_id, bid.user_id),
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
    """Get bid history for an auction, ordered by amount descending. Invalidated bids are hidden."""
    # Verify auction exists
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    # Count total using SQL COUNT instead of loading all rows
    count_result = await db.execute(
        select(func.count(Bid.id)).where(Bid.auction_id == auction_id, Bid.invalidated == False)  # noqa: E712
    )
    total_count = count_result.scalar()

    query = (
        select(Bid)
        .where(Bid.auction_id == auction_id, Bid.invalidated == False)  # noqa: E712
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
                user_name=anonymize_bidder(auction_id, b.user_id),
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
async def finalize_auction_endpoint(
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

    # Only auctions still in a biddable state can be finalized
    if auction.status not in BIDDABLE_STATUSES:
        raise HTTPException(status_code=400, detail=f"Auction is not open for bidding (status: {auction.status.value})")

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

    # Delegate to shared service (includes notifications, broadcast)
    summary = await finalize_auction(db, auction, broadcast=True)
    return summary


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
            auction_current_price=b.auction.current_price if b.auction else None,
            auction_status=b.auction.status.value if b.auction else None,
            auction_end_time=b.auction.end_time if b.auction else None,
            auction_lot_code=b.auction.lot_code if b.auction else None,
        )
        for b in bids
    ]
