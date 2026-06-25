import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.domain import Payment, PaymentStatus, Commission, User, Auction, NotificationType
from app.services.notifications import send_notification
from app.schemas.payment import PaymentCreateRequest, PaymentResponse, CommissionResponse

payments_router = APIRouter(prefix="/api/payments", tags=["payments"])


@payments_router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    req: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a payment for a completed auction (buyer only)."""
    # Verify auction exists
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

    # Check if payment already exists
    existing = await db.execute(
        select(Payment).where(Payment.auction_id == req.auction_id)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Payment already exists for this auction")

    payment = Payment(
        id=str(uuid.uuid4()),
        auction_id=req.auction_id,
        buyer_id=current_user.id,
        amount=auction.current_price,
        status=PaymentStatus.pending,
        stripe_session_id=req.stripe_session_id,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentResponse(
        id=payment.id,
        auction_id=payment.auction_id,
        buyer_id=payment.buyer_id,
        amount=payment.amount,
        status=payment.status.value if hasattr(payment.status, 'value') else str(payment.status),
        stripe_session_id=payment.stripe_session_id,
        created_at=str(payment.created_at) if payment.created_at else "",
    )


@payments_router.get("/my", response_model=list[PaymentResponse])
async def my_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's payments."""
    result = await db.execute(
        select(Payment)
        .where(Payment.buyer_id == current_user.id)
        .order_by(desc(Payment.created_at))
    )
    payments = result.scalars().all()
    return [
        PaymentResponse(
            id=p.id,
            auction_id=p.auction_id,
            buyer_id=p.buyer_id,
            amount=p.amount,
            status=p.status.value if hasattr(p.status, 'value') else str(p.status),
            stripe_session_id=p.stripe_session_id,
            created_at=str(p.created_at) if p.created_at else "",
        )
        for p in payments
    ]


# ========== ADMIN: Update payment status ==========
@payments_router.put("/{payment_id}/status", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: str,
    new_status: str = Query(..., pattern=r"^(completed|failed|refunded)$"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update payment status (admin only). When completed, creates commission."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalars().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = PaymentStatus(new_status)
    await db.commit()
    await db.refresh(payment)

    # If payment completed, create commission record
    if new_status == "completed":
        result = await db.execute(select(Auction).where(Auction.id == payment.auction_id))
        auction = result.scalars().first()
        if auction:
            commission_rate = 0.05  # 5% commission
            commission_amount = payment.amount * commission_rate
            commission = Commission(
                id=str(uuid.uuid4()),
                auction_id=payment.auction_id,
                seller_id=auction.seller_id,
                amount=commission_amount,
                rate=commission_rate,
                status=PaymentStatus.pending,
            )
            db.add(commission)
            await db.commit()

            # Notify seller and buyer
            await send_notification(
                db, auction.seller_id,
                NotificationType.payment_received,
                f"Payment received for {auction.title}",
                f"Payment of ${payment.amount:.2f} received. Commission: ${commission_amount:.2f}",
                auction_id=payment.auction_id,
                send_email=True,
            )

    return PaymentResponse(
        id=payment.id,
        auction_id=payment.auction_id,
        buyer_id=payment.buyer_id,
        amount=payment.amount,
        status=payment.status.value if hasattr(payment.status, 'value') else str(payment.status),
        stripe_session_id=payment.stripe_session_id,
        created_at=str(payment.created_at) if payment.created_at else "",
    )


# ========== ADMIN: List all payments ==========
@payments_router.get("", response_model=list[PaymentResponse])
async def admin_list_payments(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all payments (admin only)."""
    result = await db.execute(
        select(Payment).order_by(desc(Payment.created_at))
    )
    payments = result.scalars().all()
    return [
        PaymentResponse(
            id=p.id,
            auction_id=p.auction_id,
            buyer_id=p.buyer_id,
            amount=p.amount,
            status=p.status.value if hasattr(p.status, 'value') else str(p.status),
            stripe_session_id=p.stripe_session_id,
            created_at=str(p.created_at) if p.created_at else "",
        )
        for p in payments
    ]


# ========== ADMIN: List all commissions ==========
@payments_router.get("/commissions", response_model=list[CommissionResponse])
async def admin_list_commissions(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all commissions (admin only)."""
    result = await db.execute(
        select(Commission).order_by(desc(Commission.created_at))
    )
    commissions = result.scalars().all()
    return [
        CommissionResponse(
            id=c.id,
            auction_id=c.auction_id,
            seller_id=c.seller_id,
            amount=c.amount,
            rate=c.rate,
            status=c.status.value if hasattr(c.status, 'value') else str(c.status),
            created_at=str(c.created_at) if c.created_at else "",
        )
        for c in commissions
    ]
