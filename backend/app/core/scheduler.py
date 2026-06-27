import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.domain import Auction, AuctionStatus
from app.services.auctions import finalize_auction

logger = logging.getLogger("bidmont.scheduler")

FINALIZE_INTERVAL_SECONDS = 30  # Check every 30 seconds


async def _finalize_expired_auctions():
    """
    Find all active auctions whose end_time has passed and automatically
    finalize them via the shared auction service.
    """
    try:
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)

            # Find expired active auctions
            result = await db.execute(
                select(Auction)
                .options(selectinload(Auction.seller))
                .where(
                    Auction.status == AuctionStatus.active,
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