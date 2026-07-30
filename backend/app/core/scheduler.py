import asyncio
import logging
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.domain import Auction, AuctionStatus, AuctionParticipant, BIDDABLE_STATUSES, _utcnow
from app.services.auctions import finalize_auction
from app.services.notifications import send_notification, NotificationType

logger = logging.getLogger("bidmont.scheduler")

FINALIZE_INTERVAL_SECONDS = 30  # Check every 30 seconds
ENDING_SOON_THRESHOLD_SECONDS = 900  # doc §16.1 "ending soon" reminder window (15 min)


async def _finalize_expired_auctions():
    """
    Find all active auctions whose end_time has passed and automatically
    finalize them via the shared auction service.
    """
    try:
        async with AsyncSessionLocal() as db:
            now = _utcnow()

            # Promote scheduled auctions whose start_time has arrived. Committed
            # and out of the way *before* the expired-auction query below, so
            # that query's results are never touched by a session-wide commit
            # (app's AsyncSessionLocal has expire_on_commit=False, so this
            # isn't a live bug today, but keep the ordering safe regardless).
            promote_result = await db.execute(
                select(Auction).where(
                    Auction.status == AuctionStatus.upcoming,
                    Auction.start_time <= now,
                )
            )
            due_auctions = promote_result.scalars().all()
            if due_auctions:
                for auction in due_auctions:
                    auction.status = AuctionStatus.live
                await db.commit()

            # Ending-soon reminders (doc §16.1): notify everyone who joined a
            # biddable auction closing within the threshold. event_key dedupes
            # across repeated 30s polls so each participant is notified once
            # per auction (not once per poll cycle).
            # ponytail: event_key is per auction+user with no end_time component,
            # so if anti-sniping extension moves the deadline back out past the
            # threshold and it later re-enters, no second reminder fires. Add an
            # end_time component to the key if that gap matters in practice.
            soon_result = await db.execute(
                select(Auction).where(
                    Auction.status.in_(BIDDABLE_STATUSES),
                    Auction.end_time > now,
                    Auction.end_time <= now + timedelta(seconds=ENDING_SOON_THRESHOLD_SECONDS),
                )
            )
            for auction in soon_result.scalars().all():
                participants_result = await db.execute(
                    select(AuctionParticipant.user_id).where(AuctionParticipant.auction_id == auction.id)
                )
                for user_id in participants_result.scalars().all():
                    await send_notification(
                        db, user_id,
                        NotificationType.auction_ending_soon,
                        f"Ending soon: {auction.title}",
                        f"'{auction.title}' closes at {auction.end_time.isoformat()}.",
                        auction_id=auction.id,
                        send_email=True,
                        event_key=f"ending_soon:{auction.id}:{user_id}",
                        title_me=f"Uskoro se završava: {auction.title}",
                        message_me=f"'{auction.title}' se zatvara u {auction.end_time.isoformat()}.",
                    )

            # Find expired auctions still in a biddable state (live or extended)
            result = await db.execute(
                select(Auction)
                .options(selectinload(Auction.seller))
                .where(
                    Auction.status.in_(BIDDABLE_STATUSES),
                    Auction.end_time <= now,
                )
            )
            expired_auctions = result.scalars().all()

            for auction in expired_auctions:
                try:
                    summary = await finalize_auction(db, auction, broadcast=True)
                    logger.info(
                        f"Auto-finalized auction {auction.id} ('{auction.title}'). "
                        f"Winner: {summary.get('winner_user_id') or 'None'}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error finalizing auction {auction.id}: {e}",
                        exc_info=True,
                    )

    except Exception as e:
        logger.error(f"Error in finalize scheduler loop: {e}", exc_info=True)


async def run_scheduler():
    """Background task that periodically finalizes expired auctions."""
    logger.info("Starting auction finalize scheduler...")
    while True:
        await _finalize_expired_auctions()
        await asyncio.sleep(FINALIZE_INTERVAL_SECONDS)