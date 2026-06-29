import hashlib
import os
import time as _time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import User, CreditPurchase, PaymentStatus

credits_router = APIRouter(prefix="/api/credits", tags=["credits"])

PACKAGES = {
    "starter":  {"credits": 100,  "eur": 10},
    "standard": {"credits": 300,  "eur": 25},
    "pro":      {"credits": 1000, "eur": 75},
}

_MONRI_FORM_URL = {
    "production": "https://ipg.monri.com/v2/form",
    "test": "https://ipgtest.monri.com/v2/form",
}


class CheckoutRequest(BaseModel):
    package: str


def _monri_digest(merchant_key: str, order_number: str, amount_cents: int, currency: str) -> str:
    return hashlib.sha512(f"{merchant_key}{order_number}{amount_cents}{currency}".encode()).hexdigest()


def _monri_base_url() -> str:
    return _MONRI_FORM_URL.get(os.getenv("MONRI_ENV", "test"), _MONRI_FORM_URL["test"])


@credits_router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    return {"credits_balance": current_user.credits_balance or 0.0}


@credits_router.post("/monri/checkout")
async def create_monri_credit_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pkg = PACKAGES.get(req.package)
    if not pkg:
        raise HTTPException(400, f"Unknown package. Choose: {', '.join(PACKAGES)}")

    merchant_key = os.getenv("MONRI_MERCHANT_KEY")
    authenticity_token = os.getenv("MONRI_AUTHENTICITY_TOKEN")
    if not merchant_key or not authenticity_token:
        raise HTTPException(503, "Monri not configured. Set MONRI_MERCHANT_KEY and MONRI_AUTHENTICITY_TOKEN.")

    purchase_id = str(uuid.uuid4())
    order_number = f"cred-{purchase_id[:8]}-{int(_time.time())}"
    amount_cents = pkg["eur"] * 100
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")

    purchase = CreditPurchase(
        id=purchase_id,
        user_id=current_user.id,
        credits_amount=pkg["credits"],
        amount_eur=pkg["eur"],
        stripe_session_id=order_number,  # ponytail: column kept, stores Monri order_number
        status=PaymentStatus.pending,
    )
    db.add(purchase)
    await db.commit()

    form_fields = {
        "authenticity_token": authenticity_token,
        "order_number": order_number,
        "amount": str(amount_cents),
        "currency": "EUR",
        "transaction_type": "purchase",
        "order_info": f"{pkg['credits']} Credits ({req.package})",
        "digest": _monri_digest(merchant_key, order_number, amount_cents, "EUR"),
        "language": "en",
        "ch_full_name": (current_user.name or "Buyer")[:30],
        "ch_email": current_user.email,
        "ch_address": "N/A",
        "ch_city": "Podgorica",
        "ch_zip": "81000",
        "ch_country": "ME",
        "ch_phone": "N/A",
        "success_url_override": f"{frontend_url}/#profile?credits=success",
        "cancel_url_override": f"{frontend_url}/#profile",
        "callback_url_override": f"{frontend_url}/api/credits/monri/callback",
    }

    return {"checkout_url": _monri_base_url(), "form_fields": form_fields}


@credits_router.post("/monri/callback")
async def monri_credit_callback(
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

    result = await db.execute(select(CreditPurchase).where(CreditPurchase.stripe_session_id == order_number))
    purchase = result.scalars().first()
    if not purchase:
        return {"status": "ignored"}
    if purchase.status == PaymentStatus.completed:
        return {"status": "already_processed"}

    if body.get("status") == "approved" and body.get("response_code") == "0000":
        purchase.status = PaymentStatus.completed
        user_result = await db.execute(select(User).where(User.id == purchase.user_id))
        user = user_result.scalars().first()
        if user:
            user.credits_balance = (user.credits_balance or 0.0) + purchase.credits_amount
        await db.commit()

    return {"status": "ok"}
