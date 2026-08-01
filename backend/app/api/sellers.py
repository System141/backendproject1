"""Seller application API (doc §11.1/§11.2): Apply -> Admin Review -> Verified Seller.
Verification itself (and the role promotion it triggers) is an admin-only
action - see app/api/admin.py's SELLER APPLICATIONS section."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import SellerProfile, SellerVerificationStatus, User
from app.schemas.seller import SellerApplicationRequest, SellerProfileResponse
from app.services.notifications import send_notification, NotificationType

sellers_router = APIRouter(prefix="/api/sellers", tags=["sellers"])


@sellers_router.get("/me", response_model=SellerProfileResponse)
async def get_my_seller_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SellerProfile).where(SellerProfile.user_id == current_user.id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="No seller application on file")
    return profile


@sellers_router.post("/apply", response_model=SellerProfileResponse, status_code=201)
async def apply_as_seller(
    req: SellerApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit (or resubmit after rejection) a seller application. A pending or
    already-verified application can't be resubmitted - the admin review
    queue is the single place that state changes.

    Doc §11.2 lists "Phone + email verification" as a required application
    field. Email verification is enforced here (reuses the §20 AC-01 flow);
    phone/SMS verification needs an SMS gateway choice, so it isn't gated -
    see docs/proje-durum-raporu.md's C-list.
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email address before applying as a seller.",
        )

    result = await db.execute(select(SellerProfile).where(SellerProfile.user_id == current_user.id))
    profile = result.scalars().first()

    if profile:
        if profile.verification_status == SellerVerificationStatus.verified:
            raise HTTPException(status_code=409, detail="Already a verified seller")
        if profile.verification_status == SellerVerificationStatus.pending:
            raise HTTPException(status_code=409, detail="Application already pending review")
        # Rejected - allow a fresh application, replacing the prior answers
        profile.account_type = req.account_type
        profile.company_name = req.company_name
        profile.pib = req.pib
        profile.authorized_person = req.authorized_person
        profile.city = req.city
        profile.seller_type = req.seller_type
        profile.verification_status = SellerVerificationStatus.pending
        profile.rejection_reason = None
        profile.reviewed_by = None
        profile.reviewed_at = None
    else:
        profile = SellerProfile(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            account_type=req.account_type,
            company_name=req.company_name,
            pib=req.pib,
            authorized_person=req.authorized_person,
            city=req.city,
            seller_type=req.seller_type,
        )
        db.add(profile)

    await db.commit()
    await db.refresh(profile)

    await send_notification(
        db, current_user.id,
        NotificationType.seller_application_submitted,
        "Seller application submitted",
        "Your seller application was submitted and is pending admin review.",
        send_email=True,
        title_me="Prijava za prodavca poslata",
        message_me="Vaša prijava za prodavca je poslata i čeka pregled administratora.",
    )

    return profile
