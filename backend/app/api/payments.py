import hashlib
import os
import time as _time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.domain import Payment, PaymentStatus, Commission, User, Auction, NotificationType
from app.services.notifications import send_notification
from app.schemas.payment import PaymentCreateRequest, PaymentResponse, CommissionResponse

payments_router = APIRouter(prefix="/api/payments", tags=["payments"])

_MONRI_FORM_URL = {
    "production": "https://ipg.monri.com/v2/form",
    "test": "https://ipgtest.monri.com/v2/form",
}


def _monri_digest(merchant_key: str, order_number: str, amount_cents: int, currency: str) -> str:
    return hashlib.sha512(f"{merchant_key}{order_number}{amount_cents}{currency}".encode()).hexdigest()


def _monri_base_url() -> str:
    return _MONRI_FORM_URL.get(os.getenv("MONRI_ENV", "test"), _MONRI_FORM_URL["test"])


def _payment_response(p: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=p.id,
        auction_id=p.auction_id,
        buyer_id=p.buyer_id,
        amount=p.amount,
        buyer_service_fee=p.buyer_service_fee,
        status=p.status.value if hasattr(p.status, "value") else str(p.status),
        payment_session_id=p.stripe_session_id,  # ponytail: column kept, stores Monri order_number
        created_at=str(p.created_at) if p.created_at else "",
    )


@payments_router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    req: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Auction).where(Auction.id == req.auction_id))
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status.name != "completed":
        raise HTTPException(status_code=400, detail="Auction is not completed")
    if not auction.winner_user_id:
        raise HTTPException(status_code=400, detail="Auction has no winning bidder")
    if auction.winner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the winning bidder can pay for this auction")

    existing = await db.execute(select(Payment).where(Payment.auction_id == req.auction_id))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Payment already exists for this auction")

    payment = Payment(
        id=str(uuid.uuid4()),
        auction_id=req.auction_id,
        buyer_id=current_user.id,
        amount=auction.current_price,
        buyer_service_fee=round(auction.current_price * 0.03, 2),
        status=PaymentStatus.pending,
        stripe_session_id=req.payment_session_id,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return _payment_response(payment)


@payments_router.get("/my", response_model=list[PaymentResponse])
async def my_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment).where(Payment.buyer_id == current_user.id).order_by(desc(Payment.created_at))
    )
    return [_payment_response(p) for p in result.scalars().all()]


@payments_router.put("/{payment_id}/status", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: str,
    new_status: str = Query(..., pattern=r"^(completed|failed|refunded)$"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = PaymentStatus(new_status)
    await db.commit()
    await db.refresh(payment)

    if new_status == "completed":
        await _complete_payment(db, payment)

    return _payment_response(payment)


@payments_router.get("", response_model=list[PaymentResponse])
async def admin_list_payments(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).order_by(desc(Payment.created_at)))
    return [_payment_response(p) for p in result.scalars().all()]


@payments_router.get("/commissions", response_model=list[CommissionResponse])
async def admin_list_commissions(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Commission).order_by(desc(Commission.created_at)))
    commissions = result.scalars().all()
    return [
        CommissionResponse(
            id=c.id,
            auction_id=c.auction_id,
            seller_id=c.seller_id,
            amount=c.amount,
            rate=c.rate,
            status=c.status.value if hasattr(c.status, "value") else str(c.status),
            created_at=str(c.created_at) if c.created_at else "",
        )
        for c in commissions
    ]


# ========== Monri ==========

@payments_router.post("/monri/checkout")
async def create_monri_checkout(
    req: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    merchant_key = os.getenv("MONRI_MERCHANT_KEY")
    authenticity_token = os.getenv("MONRI_AUTHENTICITY_TOKEN")
    if not merchant_key or not authenticity_token:
        raise HTTPException(status_code=503, detail="Monri not configured. Set MONRI_MERCHANT_KEY and MONRI_AUTHENTICITY_TOKEN.")

    result = await db.execute(select(Auction).where(Auction.id == req.auction_id))
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.status.name != "completed":
        raise HTTPException(status_code=400, detail="Auction is not completed")
    if auction.winner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the winning bidder can initiate payment")

    existing = await db.execute(select(Payment).where(Payment.auction_id == req.auction_id))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Payment already exists for this auction")

    buyer_fee = round(auction.current_price * 0.03, 2)
    total_cents = int((auction.current_price + buyer_fee) * 100)
    order_number = f"pay-{auction.id[:8]}-{int(_time.time())}"

    payment = Payment(
        id=str(uuid.uuid4()),
        auction_id=auction.id,
        buyer_id=current_user.id,
        amount=auction.current_price,
        buyer_service_fee=buyer_fee,
        status=PaymentStatus.pending,
        stripe_session_id=order_number,
    )
    db.add(payment)
    await db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")
    form_fields = {
        "authenticity_token": authenticity_token,
        "order_number": order_number,
        "amount": str(total_cents),
        "currency": "EUR",
        "transaction_type": "purchase",
        "order_info": auction.title[:100],
        "digest": _monri_digest(merchant_key, order_number, total_cents, "EUR"),
        "language": "en",
        "ch_full_name": (current_user.name or "Buyer")[:30],
        "ch_email": current_user.email,
        "ch_address": "N/A",
        "ch_city": "Podgorica",
        "ch_zip": "81000",
        "ch_country": "ME",
        "ch_phone": "N/A",
        "success_url_override": f"{frontend_url}/#profile?payment=success&auction={auction.id}",
        "cancel_url_override": f"{frontend_url}/#detail?id={auction.id}",
        "callback_url_override": f"{frontend_url}/api/payments/monri/callback",
    }

    return {"checkout_url": _monri_base_url(), "form_fields": form_fields}


@payments_router.post("/monri/callback")
async def monri_payment_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    order_number = body.get("order_number")
    if not order_number:
        raise HTTPException(status_code=400, detail="Missing order_number")

    result = await db.execute(select(Payment).where(Payment.stripe_session_id == order_number))
    payment = result.scalars().first()
    if not payment:
        return {"status": "ignored"}
    if payment.status != PaymentStatus.pending:
        return {"status": "already_processed"}

    if body.get("status") == "approved" and body.get("response_code") == "0000":
        payment.status = PaymentStatus.completed
        await db.commit()
        await _complete_payment(db, payment)
    else:
        payment.status = PaymentStatus.failed
        await db.commit()

    return {"status": "ok"}


async def _complete_payment(db: AsyncSession, payment: Payment) -> None:
    result = await db.execute(select(Auction).where(Auction.id == payment.auction_id))
    auction = result.scalars().first()
    if not auction:
        return
    commission_rate = 0.05
    commission_amount = payment.amount * commission_rate
    db.add(Commission(
        id=str(uuid.uuid4()),
        auction_id=payment.auction_id,
        seller_id=auction.seller_id,
        amount=commission_amount,
        rate=commission_rate,
        status=PaymentStatus.pending,
    ))
    await db.commit()
    await send_notification(
        db, auction.seller_id,
        NotificationType.payment_received,
        f"Payment received for {auction.title}",
        f"Payment of €{payment.amount:.2f} received. Commission: €{commission_amount:.2f}",
        auction_id=payment.auction_id,
        send_email=True,
    )
