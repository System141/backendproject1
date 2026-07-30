"""
Credit ledger service: the single place a user's credit balance is mutated.

Every change (purchase, join-auction spend, admin adjustment, reversal) goes
through apply_ledger_entry so credits_balance stays a reconstructible cache
of the CreditLedger, the same way current_price is a cache of valid Bids.
"""
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import CreditLedger, CreditLedgerType, TermsDocument, User


async def apply_ledger_entry(
    db: AsyncSession,
    user: User,
    delta: float,
    type: CreditLedgerType,
    reference: str | None = None,
    reason: str | None = None,
    actor_id: str | None = None,
) -> CreditLedger:
    """
    Apply a +/- credit delta to user.credits_balance and record it as an
    immutable CreditLedger row. Raises 402 if the resulting balance would go
    negative. Does not commit - the caller commits as part of its own
    transaction (e.g. alongside an AuctionParticipant insert).
    """
    result = await db.execute(select(User).where(User.id == user.id).with_for_update())
    locked_user = result.scalars().first()

    balance_before = locked_user.credits_balance or 0.0
    balance_after = balance_before + delta
    if balance_after < 0:
        raise HTTPException(status_code=402, detail="Insufficient credit balance")

    entry = CreditLedger(
        user_id=locked_user.id,
        type=type,
        amount=delta,
        reference=reference,
        balance_before=balance_before,
        balance_after=balance_after,
        actor_id=actor_id,
        reason=reason,
    )
    db.add(entry)
    locked_user.credits_balance = balance_after
    return entry


CREDIT_TERMS_TEXT = (
    "BidMont credits are used solely to unlock participation in a specific "
    "auction and are not a payment toward the listed asset. Credits are "
    "non-transferable and non-refundable once spent to join an auction, "
    "except where a BidMont-initiated cancellation triggers an automatic "
    "reversal. Purchased but unused credits may be refunded per the Credit "
    "Purchase / Refund & Cancellation Policy."
)
CREDIT_TERMS_VERSION = "1.0"


async def get_or_create_credit_terms(db: AsyncSession) -> TermsDocument:
    """Doc §15.2 requires an acceptance record for the Credit Terms/Refund
    policy before a checkout order is created. Same idempotent
    get-or-create shape as get_or_create_seller_declaration - auto-provision
    app-copy placeholder now; LITZOR's counsel-approved final text (§21.1)
    replaces the content later without touching this version-tracking
    mechanism."""
    result = await db.execute(
        select(TermsDocument).where(
            TermsDocument.document_type == "credit_terms",
            TermsDocument.is_active == True,  # noqa: E712
        )
    )
    doc = result.scalars().first()
    if doc:
        return doc
    try:
        async with db.begin_nested():
            db.add(TermsDocument(
                id=str(uuid.uuid4()),
                document_type="credit_terms",
                version=CREDIT_TERMS_VERSION,
                content=CREDIT_TERMS_TEXT,
                is_active=True,
            ))
    except IntegrityError:
        pass  # concurrent request already created it
    result = await db.execute(
        select(TermsDocument).where(
            TermsDocument.document_type == "credit_terms",
            TermsDocument.is_active == True,  # noqa: E712
        )
    )
    return result.scalars().first()
