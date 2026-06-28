import os
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


class CheckoutRequest(BaseModel):
    package: str


@credits_router.get("/balance")
async def get_balance(current_user: User = Depends(get_current_user)):
    return {"credits_balance": current_user.credits_balance or 0.0}


@credits_router.post("/checkout")
async def create_credit_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pkg = PACKAGES.get(req.package)
    if not pkg:
        raise HTTPException(400, f"Unknown package. Choose: {', '.join(PACKAGES)}")

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise HTTPException(503, "Stripe not configured. Set STRIPE_SECRET_KEY.")

    import stripe
    stripe.api_key = stripe_key

    purchase_id = str(uuid.uuid4())
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8000")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {"name": f"{pkg['credits']} Credits ({req.package})"},
                "unit_amount": pkg["eur"] * 100,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{frontend_url}/#profile?credits=success",
        cancel_url=f"{frontend_url}/#profile",
        metadata={
            "type": "credit_purchase",
            "purchase_id": purchase_id,
            "user_id": current_user.id,
            "credits": str(pkg["credits"]),
        },
    )

    purchase = CreditPurchase(
        id=purchase_id,
        user_id=current_user.id,
        credits_amount=pkg["credits"],
        amount_eur=pkg["eur"],
        stripe_session_id=session.id,
        status=PaymentStatus.pending,
    )
    db.add(purchase)
    await db.commit()

    return {"checkout_url": session.url, "session_id": session.id}


@credits_router.post("/webhook")
async def stripe_credit_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    if not webhook_secret:
        raise HTTPException(400, "Webhook secret not configured")

    import stripe

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
    except Exception as e:
        raise HTTPException(400, f"Webhook error: {e}")

    if event["type"] != "checkout.session.completed":
        return {"status": "ignored"}

    session = event["data"]["object"]
    meta = session.get("metadata", {})
    if meta.get("type") != "credit_purchase":
        return {"status": "ignored"}

    purchase_id = meta.get("purchase_id")
    user_id = meta.get("user_id")
    credits = float(meta.get("credits", 0))

    # Mark purchase completed
    result = await db.execute(select(CreditPurchase).where(CreditPurchase.id == purchase_id))
    purchase = result.scalars().first()
    if purchase and purchase.status != PaymentStatus.completed:
        purchase.status = PaymentStatus.completed

        # Credit the user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalars().first()
        if user:
            user.credits_balance = (user.credits_balance or 0.0) + credits

        await db.commit()

    return {"status": "ok"}
