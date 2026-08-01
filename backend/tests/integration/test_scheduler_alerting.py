"""Doc §19.7: bid-engine error alert. If finalize_auction() raises while the
scheduler tries to auto-close an expired auction, every admin must get an
alert (in addition to the existing error log)."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.core.scheduler as scheduler_module
from tests.conftest import TestSessionLocal
from app.models.domain import Auction, AuctionStatus, Category, Notification, NotificationType, User


class TestSchedulerBidEngineAlert:
    async def test_finalize_error_alerts_admins(
        self, monkeypatch, db_session: AsyncSession, admin_user: User, seller_user: User, test_category: Category,
    ):
        monkeypatch.setattr(scheduler_module, "AsyncSessionLocal", TestSessionLocal)

        async def _broken_finalize(db, auction, broadcast=True):
            raise RuntimeError("simulated bid engine failure")
        monkeypatch.setattr(scheduler_module, "finalize_auction", _broken_finalize)

        auction = Auction(
            id=str(uuid.uuid4()),
            seller_id=seller_user.id,
            category_id=test_category.id,
            title="Expired Auction",
            description="desc",
            start_price=100.0,
            current_price=100.0,
            min_increment=10.0,
            start_time=datetime.now(timezone.utc) - timedelta(days=2),
            end_time=datetime.now(timezone.utc) - timedelta(minutes=1),
            status=AuctionStatus.live,
        )
        db_session.add(auction)
        await db_session.commit()

        await scheduler_module._finalize_expired_auctions()

        result = await db_session.execute(
            select(Notification).where(Notification.user_id == admin_user.id, Notification.type == NotificationType.system_alert)
        )
        alerts = result.scalars().all()
        assert len(alerts) == 1
        assert auction.id in alerts[0].message
