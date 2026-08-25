import hashlib
import hmac
import json
import os
import time as _time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc, update

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import User, CreditPurchase, CreditPackage, CreditLedger, CreditLedgerType, PaymentStatus, TermsAcceptance
from app.schemas.credit import CreditLedgerEntryResponse
from app.services.credits import apply_ledger_entry, get_or_create_credit_terms
from app.services.notifications import send_notification, alert_admins, NotificationType

credits_router = APIRouter(prefix="/api/credits", tags=["credits"])

_MONRI_FORM_URL = {
    "production": "https://ipg.monri.com/v2/form",
    "test": "https://ipgtest.monri.com/v2/form",
}


class CheckoutRequest(BaseModel):
    package_id: str
    terms_accepted: bool = False
    return_auction_id: str | None = None


def _monri_digest(merchant_key: str, order_number: str, amount_cents: int, currency: str) -> str:
    return hashlib.sha512(f"{merchant_key}{order_number}{amount_cents}{currency}".encode()).hexdigest()


def _monri_base_url() -> str:
    return _MONRI_FORM_URL.get(os.getenv("MONRI_ENV", "test"), _MONRI_FORM_URL["test"])


def _simulate_enabled() -> bool:
    """Test-only bypass: lets credit purchases be exercised end-to-end on a
    live/running site without real Monri merchant credentials. Explicit and
    independent of whether MONRI_* is set, so a missing/typo'd credential in
    production still fails loudly (503) instead of silently faking payments.
    NEVER set PAYMENTS_SIMULATE=true in production."""
    return os.getenv("PAYMENTS_SIMULATE", "").lower() == "true"


class SimulateCompleteRequest(BaseModel):
    purchase_id: str
    approved: bool = True


@credits_router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    return {"credits_balance": current_user.credits_balance or 0.0}


@credits_router.get("/ledger", response_model=list[CreditLedgerEntryResponse])
async def get_my_ledger(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Doc §8.1: transaction history for the current user's own credit balance."""
    result = await db.execute(
        select(CreditLedger)
        .where(CreditLedger.user_id == current_user.id)
        .order_by(desc(CreditLedger.created_at))
        .limit(min(limit, 200))
    )
    return result.scalars().all()


@credits_router.get("/packages")
async def list_packages(db: AsyncSession = Depends(get_db)):
    """Public credit-store listing. Admin-managed - never hardcode prices client-side."""
    result = await db.execute(
        select(CreditPackage).where(CreditPackage.active == True).order_by(asc(CreditPackage.sort_order))  # noqa: E712
    )
    packages = result.scalars().all()
    return [
        {"id": p.id, "name": p.name, "credits": p.credits, "price_eur": p.price_eur}
        for p in packages
    ]


@credits_router.post("/monri/checkout")
async def create_monri_credit_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CreditPackage).where(CreditPackage.id == req.package_id, CreditPackage.active == True))  # noqa: E712
    pkg = result.scalars().first()
    if not pkg:
        raise HTTPException(400, "Unknown or inactive credit package")

    if not req.terms_accepted:
        raise HTTPException(400, "You must accept the Credit Terms / Refund Policy before checkout.")
    credit_terms = await get_or_create_credit_terms(db)
    db.add(TermsAcceptance(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        document_type=credit_terms.document_type,
        version=credit_terms.version,
    ))

    simulate = _simulate_enabled()
    merchant_key = os.getenv("MONRI_MERCHANT_KEY")
    authenticity_token = os.getenv("MONRI_AUTHENTICITY_TOKEN")
    if not simulate and (not merchant_key or not authenticity_token):
        raise HTTPException(503, "Monri not configured. Set MONRI_MERCHANT_KEY and MONRI_AUTHENTICITY_TOKEN.")

    purchase_id = str(uuid.uuid4())
    order_number = f"cred-{purchase_id[:8]}-{int(_time.time())}"
    amount_cents = int(round(pkg.price_eur * 100))
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")

    purchase = CreditPurchase(
        id=purchase_id,
        user_id=current_user.id,
        credits_amount=pkg.credits,
        amount_eur=pkg.price_eur,
        stripe_session_id=order_number,  # ponytail: column kept, stores Monri order_number
        status=PaymentStatus.pending,
    )
    db.add(purchase)
    await db.commit()

    if simulate:
        # Test mode: no real gateway round-trip. Frontend calls
        # POST /credits/simulate/complete next (see that endpoint below).
        return {"simulate": True, "purchase_id": purchase_id, "credits": pkg.credits, "package_name": pkg.name}

    # §8.7: after buying credits to cover an insufficient-balance join, send the
    # user back to the auction they were trying to join instead of a generic
    # profile page. Validated as a UUID so an arbitrary string can't be smuggled
    # into the redirect URL Monri sends the browser to.
    success_target = "#profile?credits=success"
    if req.return_auction_id:
        try:
            uuid.UUID(req.return_auction_id)
            success_target = f"#detail?id={req.return_auction_id}&credits=success"
        except ValueError:
            pass

    form_fields = {
        "authenticity_token": authenticity_token,
        "order_number": order_number,
        "amount": str(amount_cents),
        "currency": "EUR",
        "transaction_type": "purchase",
        "order_info": f"{pkg.credits:.0f} Credits ({pkg.name})",
        "digest": _monri_digest(merchant_key, order_number, amount_cents, "EUR"),
        "language": "en",
        "ch_full_name": (current_user.name or "Buyer")[:30],
        "ch_email": current_user.email,
        "ch_address": "N/A",
        "ch_city": "Podgorica",
        "ch_zip": "81000",
        "ch_country": "ME",
        "ch_phone": "N/A",
        "success_url_override": f"{frontend_url}/{success_target}",
        "cancel_url_override": f"{frontend_url}/#profile",
        "callback_url_override": f"{frontend_url}/api/credits/monri/callback",
    }

    return {"checkout_url": _monri_base_url(), "form_fields": form_fields}


@credits_router.post("/simulate/complete")
async def simulate_credit_purchase(
    req: SimulateCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test-only: completes a pending purchase created by the `simulate`
    branch of /monri/checkout above, without a real gateway round-trip. 404s
    (not 403) when disabled so the endpoint doesn't reveal itself outside
    test mode."""
    if not _simulate_enabled():
        raise HTTPException(404)
    result = await db.execute(
        select(CreditPurchase).where(CreditPurchase.id == req.purchase_id, CreditPurchase.user_id == current_user.id)
    )
    purchase = result.scalars().first()
    if not purchase:
        raise HTTPException(404, "Purchase not found")
    if purchase.status != PaymentStatus.pending:
        return {"status": "already_processed"}
    return {"status": await _finalize_credit_purchase(db, purchase, req.approved)}


def _verify_monri_callback_signature(raw_body: bytes, auth_header: str | None, merchant_key: str) -> bool:
    """Per Monri's callback spec (docs.monri.com/docs/how-to-calculate-digest):
    the merchant server receives an `authorization` header shaped
    `WP3-callback <digest>` where digest = sha512(merchant_key + raw_body),
    computed over the exact raw request bytes (not re-serialized JSON)."""
    prefix = "WP3-callback "
    if not auth_header or not auth_header.startswith(prefix):
        return False
    provided = auth_header[len(prefix):].strip()
    expected = hashlib.sha512(merchant_key.encode() + raw_body).hexdigest()
    return hmac.compare_digest(provided, expected)


@credits_router.post("/monri/callback")
async def monri_credit_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Doc §8.4/security review: without this, anyone who knows an
    # order_number (returned to their own browser at checkout time) could
    # POST a fabricated "approved" callback directly and credit themselves
    # without ever paying. Verify Monri's signature BEFORE trusting anything
    # in the body - raw bytes read once since the digest is over the exact
    # wire payload, not a re-serialized dict.
    merchant_key = os.getenv("MONRI_MERCHANT_KEY")
    if not merchant_key:
        raise HTTPException(status_code=503, detail="Monri not configured")

    raw_body = await request.body()
    auth_header = request.headers.get("authorization") or request.headers.get("http_authorization")
    if not _verify_monri_callback_signature(raw_body, auth_header, merchant_key):
        raise HTTPException(status_code=401, detail="Invalid callback signature")

    try:
        body = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    order_number = body.get("order_number")
    if not order_number:
        raise HTTPException(status_code=400, detail="Missing order_number")

    result = await db.execute(select(CreditPurchase).where(CreditPurchase.stripe_session_id == order_number))
    purchase = result.scalars().first()
    if not purchase:
        return {"status": "ignored"}
    if purchase.status != PaymentStatus.pending:
        return {"status": "already_processed"}

    approved = body.get("status") == "approved" and body.get("response_code") == "0000"
    return {"status": await _finalize_credit_purchase(db, purchase, approved)}


async def _finalize_credit_purchase(db: AsyncSession, purchase: CreditPurchase, approved: bool) -> str:
    """Shared by the real Monri webhook above and the test-mode
    /simulate/complete endpoint, so both paths credit the ledger and notify
    identically - one place, not two copies that can drift.

    Doc §8.4/AC-02: the gateway can deliver its callback more than once
    concurrently. A plain read-then-write status check has a race window
    where both deliveries pass the check above before either commits. This
    conditional UPDATE (status='pending' -> X) is atomic at the DB level:
    only the caller that actually flips the row proceeds to credit the
    ledger; a losing concurrent caller sees rowcount 0 and backs off.
    """
    target_status = PaymentStatus.completed if approved else PaymentStatus.failed
    claim = await db.execute(
        update(CreditPurchase)
        .where(CreditPurchase.id == purchase.id, CreditPurchase.status == PaymentStatus.pending)
        .values(status=target_status)
    )
    await db.commit()
    if claim.rowcount == 0:
        return "already_processed"
    purchase.status = target_status

    if target_status == PaymentStatus.completed:
        user_result = await db.execute(select(User).where(User.id == purchase.user_id))
        user = user_result.scalars().first()
        if user:
            await apply_ledger_entry(
                db, user, purchase.credits_amount, CreditLedgerType.purchase, reference=purchase.id,
            )
        await db.commit()
        await send_notification(
            db, purchase.user_id,
            NotificationType.credit_purchase_successful,
            "Credit purchase successful",
            f"{purchase.credits_amount:.0f} credits were added to your account.",
            send_email=True,
            event_key=f"credit_purchase:{purchase.id}:completed",
            title_me="Kupovina kredita uspješna",
            message_me=f"{purchase.credits_amount:.0f} kredita je dodato na vaš račun.",
            template_vars={"credits_amount": f"{purchase.credits_amount:.0f}"},
        )
    else:
        await send_notification(
            db, purchase.user_id,
            NotificationType.credit_purchase_failed,
            "Credit purchase failed",
            f"Your purchase of {purchase.credits_amount:.0f} credits could not be completed.",
            send_email=True,
            event_key=f"credit_purchase:{purchase.id}:failed",
            title_me="Kupovina kredita neuspješna",
            message_me=f"Vaša kupovina od {purchase.credits_amount:.0f} kredita nije mogla biti završena.",
            template_vars={"credits_amount": f"{purchase.credits_amount:.0f}"},
        )
        # doc §19.7: payment webhook failure alert - a declined/failed
        # gateway callback is worth an ops look (fraud pattern, gateway
        # misconfig), distinct from the routine user-facing notice above.
        await alert_admins(
            db,
            f"Payment webhook failure: order {purchase.stripe_session_id}",
            f"Payment callback reported a failed/declined payment for order "
            f"'{purchase.stripe_session_id}' (purchase {purchase.id}, user {purchase.user_id}, "
            f"{purchase.credits_amount:.0f} credits).",
            event_key=f"payment_webhook_failed:{purchase.id}",
        )

    return "ok"
