"""Integration tests for the credit ledger + join/bid engine (BidMont Phase 1)."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.domain import (
    Auction, AuctionStatus, AuctionParticipant, Bid, Category, CreditPackage, CreditPurchase,
    PaymentStatus, TermsAcceptance, User, UserRole,
)
from app.core.security import create_access_token, hash_password


async def _make_buyer(db_session: AsyncSession, credits: float = 0.0) -> User:
    buyer = User(
        id=str(uuid.uuid4()),
        name="Buyer",
        email=f"buyer_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("BuyerPass123!"),
        role=UserRole.buyer,
        status="active",
        accepted_terms=True,
        accepted_privacy=True,
        marketing_consent=False,
        credits_balance=credits,
    )
    db_session.add(buyer)
    await db_session.commit()
    await db_session.refresh(buyer)
    return buyer


def _headers(user: User) -> dict:
    token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


async def _make_active_auction(db_session: AsyncSession, seller: User, category: Category, **overrides) -> Auction:
    defaults = dict(
        id=str(uuid.uuid4()),
        seller_id=seller.id,
        category_id=category.id,
        title="Engine Test Auction",
        description="Credit engine coverage",
        start_price=1000.0,
        current_price=1000.0,
        min_increment=50.0,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc) + timedelta(days=7),
        status=AuctionStatus.live,
        participation_credit_cost=10.0,
    )
    defaults.update(overrides)
    auction = Auction(**defaults)
    db_session.add(auction)
    await db_session.commit()
    await db_session.refresh(auction)
    return auction


class TestJoinAuction:
    async def test_join_spends_credit_once(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category,
    ):
        buyer = await _make_buyer(db_session, credits=50.0)
        auction = await _make_active_auction(db_session, seller_user, test_category)

        response = await async_client.post(f"/api/auctions/{auction.id}/join", headers=_headers(buyer))
        assert response.status_code == 200
        data = response.json()
        assert data["already_joined"] is False
        assert data["credits_spent"] == 10.0

        await db_session.refresh(buyer)
        assert buyer.credits_balance == 40.0

        # Calling join again is a no-op: no second charge.
        response2 = await async_client.post(f"/api/auctions/{auction.id}/join", headers=_headers(buyer))
        assert response2.status_code == 200
        assert response2.json()["already_joined"] is True

        await db_session.refresh(buyer)
        assert buyer.credits_balance == 40.0

        count_result = await db_session.execute(
            select(AuctionParticipant).where(AuctionParticipant.auction_id == auction.id, AuctionParticipant.user_id == buyer.id)
        )
        assert len(count_result.scalars().all()) == 1

    async def test_join_insufficient_balance_returns_402(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category,
    ):
        buyer = await _make_buyer(db_session, credits=5.0)
        auction = await _make_active_auction(db_session, seller_user, test_category)

        response = await async_client.post(f"/api/auctions/{auction.id}/join", headers=_headers(buyer))
        assert response.status_code == 402

        count_result = await db_session.execute(
            select(AuctionParticipant).where(AuctionParticipant.auction_id == auction.id, AuctionParticipant.user_id == buyer.id)
        )
        assert count_result.scalars().first() is None


class TestCreditLedgerHistory:
    """Doc §8.1: a user can retrieve their own credit transaction history."""

    async def test_ledger_reflects_join_spend_and_is_owner_scoped(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category,
    ):
        buyer = await _make_buyer(db_session, credits=50.0)
        other = await _make_buyer(db_session, credits=50.0)
        auction = await _make_active_auction(db_session, seller_user, test_category)

        join_resp = await async_client.post(f"/api/auctions/{auction.id}/join", headers=_headers(buyer))
        assert join_resp.status_code == 200

        resp = await async_client.get("/api/credits/ledger", headers=_headers(buyer))
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) == 1
        assert entries[0]["type"] == "join_spend"
        assert entries[0]["amount"] == -10.0
        assert entries[0]["balance_before"] == 50.0
        assert entries[0]["balance_after"] == 40.0
        assert entries[0]["reference"] == auction.id

        # A different user sees no entries - the ledger is scoped to the caller.
        other_resp = await async_client.get("/api/credits/ledger", headers=_headers(other))
        assert other_resp.status_code == 200
        assert other_resp.json() == []

    async def test_ledger_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/api/credits/ledger")
        assert resp.status_code == 401


class TestJoinGateOnBid:
    async def test_bid_without_join_is_403(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category,
    ):
        buyer = await _make_buyer(db_session, credits=50.0)
        auction = await _make_active_auction(db_session, seller_user, test_category)

        response = await async_client.post(
            f"/api/auctions/{auction.id}/bids", json={"amount": 1100.0}, headers=_headers(buyer)
        )
        assert response.status_code == 403

    async def test_bid_after_join_succeeds(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category,
    ):
        buyer = await _make_buyer(db_session, credits=50.0)
        auction = await _make_active_auction(db_session, seller_user, test_category)

        join_resp = await async_client.post(f"/api/auctions/{auction.id}/join", headers=_headers(buyer))
        assert join_resp.status_code == 200

        bid_resp = await async_client.post(
            f"/api/auctions/{auction.id}/bids", json={"amount": 1100.0}, headers=_headers(buyer)
        )
        assert bid_resp.status_code == 201


class TestBidIdempotency:
    async def test_retried_bid_returns_same_bid(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, test_category: Category,
    ):
        buyer = await _make_buyer(db_session, credits=50.0)
        auction = await _make_active_auction(db_session, seller_user, test_category)
        await async_client.post(f"/api/auctions/{auction.id}/join", headers=_headers(buyer))

        payload = {"amount": 1100.0, "idempotency_key": "retry-key-1"}
        first = await async_client.post(f"/api/auctions/{auction.id}/bids", json=payload, headers=_headers(buyer))
        assert first.status_code == 201
        second = await async_client.post(f"/api/auctions/{auction.id}/bids", json=payload, headers=_headers(buyer))
        assert second.status_code == 201
        assert second.json()["id"] == first.json()["id"]

        count_result = await db_session.execute(select(Bid).where(Bid.auction_id == auction.id))
        assert len(count_result.scalars().all()) == 1


class TestCreditWebhookIdempotency:
    async def test_retried_webhook_credits_once(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User,
    ):
        purchase = CreditPurchase(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            credits_amount=100.0,
            amount_eur=10.0,
            stripe_session_id="order-retry-1",
            status=PaymentStatus.pending,
        )
        db_session.add(purchase)
        await db_session.commit()

        body = {"order_number": "order-retry-1", "status": "approved", "response_code": "0000"}
        for _ in range(3):
            resp = await async_client.post("/api/credits/monri/callback", json=body)
            assert resp.status_code == 200

        await db_session.refresh(test_user)
        assert test_user.credits_balance == 100.0


class TestCreditCheckoutTermsAcceptance:
    async def test_checkout_requires_terms_acceptance(
        self, async_client: AsyncClient, db_session: AsyncSession, test_user: User, monkeypatch,
    ):
        """Doc §15.2: checkout must record consent before creating an order."""
        monkeypatch.setenv("MONRI_MERCHANT_KEY", "test-key")
        monkeypatch.setenv("MONRI_AUTHENTICITY_TOKEN", "test-token")

        pkg = CreditPackage(id=str(uuid.uuid4()), name="Starter", credits=100.0, price_eur=10.0, active=True)
        db_session.add(pkg)
        await db_session.commit()

        headers = _headers(test_user)

        rejected = await async_client.post(
            "/api/credits/monri/checkout", json={"package_id": pkg.id, "terms_accepted": False}, headers=headers,
        )
        assert rejected.status_code == 400

        accepted = await async_client.post(
            "/api/credits/monri/checkout", json={"package_id": pkg.id, "terms_accepted": True}, headers=headers,
        )
        assert accepted.status_code == 200

        result = await db_session.execute(
            select(TermsAcceptance).where(
                TermsAcceptance.user_id == test_user.id,
                TermsAcceptance.document_type == "credit_terms",
            )
        )
        assert len(result.scalars().all()) == 1


class TestFinalizeTieBreak:
    async def test_earlier_bid_wins_tie(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, seller_headers: dict, test_category: Category,
    ):
        auction = await _make_active_auction(
            db_session, seller_user, test_category,
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        earlier_bidder = await _make_buyer(db_session)
        later_bidder = await _make_buyer(db_session)

        now = datetime.now(timezone.utc)
        db_session.add(Bid(
            id=str(uuid.uuid4()), auction_id=auction.id, user_id=earlier_bidder.id,
            amount=1200.0, created_at=now - timedelta(minutes=5),
        ))
        db_session.add(Bid(
            id=str(uuid.uuid4()), auction_id=auction.id, user_id=later_bidder.id,
            amount=1200.0, created_at=now - timedelta(minutes=1),
        ))
        await db_session.commit()

        response = await async_client.post(f"/api/auctions/{auction.id}/finalize", headers=seller_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["winner_user_id"] == earlier_bidder.id
        assert "payment" not in data


class TestAdminInvalidateBid:
    async def test_invalidate_recomputes_current_price(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, admin_headers: dict, test_category: Category,
    ):
        auction = await _make_active_auction(db_session, seller_user, test_category)
        buyer_low = await _make_buyer(db_session)
        buyer_high = await _make_buyer(db_session)

        low_bid = Bid(id=str(uuid.uuid4()), auction_id=auction.id, user_id=buyer_low.id, amount=1100.0)
        high_bid = Bid(id=str(uuid.uuid4()), auction_id=auction.id, user_id=buyer_high.id, amount=1200.0)
        db_session.add_all([low_bid, high_bid])
        await db_session.commit()

        response = await async_client.post(
            f"/api/admin/bids/{high_bid.id}/invalidate", json={"reason": "fraud check"}, headers=admin_headers,
        )
        assert response.status_code == 200

        await db_session.refresh(auction)
        assert auction.current_price == 1100.0

        history = await async_client.get(f"/api/auctions/{auction.id}/bids")
        amounts = [b["amount"] for b in history.json()["bids"]]
        assert 1200.0 not in amounts


class TestAdminCancelAuction:
    async def test_cancel_reverses_participant_credits(
        self, async_client: AsyncClient, db_session: AsyncSession, seller_user: User, admin_headers: dict, test_category: Category,
    ):
        buyer = await _make_buyer(db_session, credits=50.0)
        auction = await _make_active_auction(db_session, seller_user, test_category)
        await async_client.post(f"/api/auctions/{auction.id}/join", headers=_headers(buyer))
        await db_session.refresh(buyer)
        assert buyer.credits_balance == 40.0

        response = await async_client.post(
            f"/api/admin/auctions/{auction.id}/cancel", json={"reason": "seller withdrew listing"}, headers=admin_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

        await db_session.refresh(buyer)
        assert buyer.credits_balance == 50.0
