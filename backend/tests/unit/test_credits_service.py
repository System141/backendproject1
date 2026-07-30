"""Unit tests for the credit ledger service and bid increment lookup."""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import User, CreditLedgerType, BidIncrementRule
from app.services.credits import apply_ledger_entry
from app.services.auctions import get_bid_increment


class TestApplyLedgerEntry:
    async def test_credit_increases_balance_and_records_ledger(self, db_session: AsyncSession, test_user: User):
        entry = await apply_ledger_entry(db_session, test_user, 50.0, CreditLedgerType.purchase, reference="order-1")
        await db_session.commit()

        assert entry.balance_before == 0.0
        assert entry.balance_after == 50.0
        assert entry.amount == 50.0
        assert entry.type == CreditLedgerType.purchase
        await db_session.refresh(test_user)
        assert test_user.credits_balance == 50.0

    async def test_debit_reduces_balance(self, db_session: AsyncSession, test_user: User):
        await apply_ledger_entry(db_session, test_user, 100.0, CreditLedgerType.purchase)
        await db_session.commit()

        entry = await apply_ledger_entry(db_session, test_user, -30.0, CreditLedgerType.join_spend, reference="auction-1")
        await db_session.commit()

        assert entry.balance_before == 100.0
        assert entry.balance_after == 70.0
        await db_session.refresh(test_user)
        assert test_user.credits_balance == 70.0

    async def test_insufficient_balance_raises_402(self, db_session: AsyncSession, test_user: User):
        with pytest.raises(HTTPException) as exc_info:
            await apply_ledger_entry(db_session, test_user, -10.0, CreditLedgerType.join_spend)
        assert exc_info.value.status_code == 402
        await db_session.refresh(test_user)
        assert (test_user.credits_balance or 0.0) == 0.0

    async def test_admin_adjust_records_reason_and_actor(self, db_session: AsyncSession, test_user: User, admin_user: User):
        entry = await apply_ledger_entry(
            db_session, test_user, 25.0, CreditLedgerType.admin_adjust,
            reason="goodwill credit", actor_id=admin_user.id,
        )
        await db_session.commit()

        assert entry.reason == "goodwill credit"
        assert entry.actor_id == admin_user.id


class TestGetBidIncrement:
    async def test_falls_back_when_no_rules(self, db_session: AsyncSession):
        increment = await get_bid_increment(db_session, current_price=1000.0, fallback=50.0)
        assert increment == 50.0

    async def test_picks_highest_threshold_at_or_below_price(self, db_session: AsyncSession):
        db_session.add_all([
            BidIncrementRule(min_price=0, increment=25),
            BidIncrementRule(min_price=1000, increment=50),
            BidIncrementRule(min_price=5000, increment=100),
        ])
        await db_session.commit()

        assert await get_bid_increment(db_session, current_price=500.0, fallback=999) == 25
        assert await get_bid_increment(db_session, current_price=1000.0, fallback=999) == 50
        assert await get_bid_increment(db_session, current_price=4999.0, fallback=999) == 50
        assert await get_bid_increment(db_session, current_price=5000.0, fallback=999) == 100
