"""
Auction service: shared business logic used by both the REST endpoints and the scheduler.

Consolidates finalize logic, auction response building, and common helpers
so that API routers and the background scheduler call the same code.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import (
    Auction, AuctionStatus, Bid, User, Payment, PaymentStatus, NotificationType,
)
from app.services.notifications import send_notification
from app.schemas.auction import AuctionResponse

logger = logging.getLogger("bidmont.auction_service")


async def finalize_auction(
    db: AsyncSession,
    auction: Auction,
    broadcast: bool = True,
) -> dict:
    """
    Finalize an ended auction:
    - Determine the highest bidder (if any).
    - Mark auction as completed.
    - Create payment record for winner.
    - Notify seller, winner, and losing bidders.
    - Optionally broadcast via WebSocket.

    Returns a summary dict.
    """
    # Find the highest bid
    bid_result = await db.execute(
        select(Bid)
        .where(Bid.auction_id == auction.id)
        .order_by(desc(Bid.amount))
        .limit(1)
    )
    highest_bid = bid_result.scalars().first()

    winner_id = highest_bid.user_id if highest_bid else None

    auction.status = AuctionStatus.completed
    auction.winner_user_id = winner_id

    # Notify winner and create payment record
    if winner_id and highest_bid:
        winner_user = await db.execute(
            select(User).where(User.id == winner_id)
        )
        winner_user_obj = winner_user.scalars().first()
        if winner_user_obj:
            await send_notification(
                db, winner_id,
                NotificationType.auction_won,
                f"You won: {auction.title}",
                f"Congratulations! You won the auction '{auction.title}' with a bid of ${highest_bid.amount:.2f}.",
                auction_id=auction.id,
                send_email=True,
            )

        # Create pending payment record for winner
        payment = Payment(
            id=str(uuid.uuid4()),
            auction_id=auction.id,
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
        auction_id=auction.id,
        send_email=True,
    )

    # Notify other bidders they lost
    if highest_bid:
        other_bidders_result = await db.execute(
            select(Bid.user_id)
            .where(
                Bid.auction_id == auction.id,
                Bid.user_id != winner_id,
            )
            .distinct()
        )
        other_bidder_ids = other_bidders_result.scalars().all()
        for loser_id in other_bidder_ids:
            await send_notification(
                db, loser_id,
                NotificationType.auction_lost,
                f"Auction ended: {auction.title}",
                f"The auction '{auction.title}' has ended. Another user won with a bid of ${highest_bid.amount:.2f}.",
                auction_id=auction.id,
                send_email=False,
            )

    # Broadcast auction status change via WebSocket
    if broadcast:
        from app.api.ws import manager
        await manager.broadcast(auction.id, {
            "type": "auction_status_changed",
            "auction_id": auction.id,
            "status": "completed",
            "winner_user_id": winner_id,
            "winning_bid": highest_bid.amount if highest_bid else None,
        })

    await db.commit()

    logger.info(
        f"Finalized auction {auction.id} ('{auction.title}'). "
        f"Winner: {winner_id or 'None'}"
    )

    return {
        "status": "completed",
        "auction_id": auction.id,
        "winner_user_id": winner_id,
        "winning_bid": highest_bid.amount if highest_bid else None,
        "has_bids": highest_bid is not None,
    }


def build_auction_response(auction: Auction) -> AuctionResponse:
    """Build an AuctionResponse from an Auction ORM instance."""
    return AuctionResponse(
        id=auction.id,
        seller_id=auction.seller_id,
        seller_name=auction.seller.name if hasattr(auction, 'seller') and auction.seller else None,
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
        is_featured=bool(auction.is_featured) if auction.is_featured is not None else False,
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