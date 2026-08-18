"""Seller application API (doc §11.1/§11.2): Apply -> Admin Review -> Verified Seller.
Verification itself (and the role promotion it triggers) is an admin-only
action - see app/api/admin.py's SELLER APPLICATIONS section."""
import os
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import SellerProfile, SellerVerificationStatus, User
from app.schemas.seller import SellerApplicationRequest, SellerProfileResponse
from app.services.notifications import send_notification, NotificationType
from app.api.uploads import ALLOWED_DOCUMENT_TYPES, MAX_FILE_SIZE, PRIVATE_UPLOAD_DIR

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


@sellers_router.post("/me/verification-document", response_model=SellerProfileResponse)
async def upload_verification_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Doc §11.2/§11.3: corporate verification document (registration
    certificate, authorized-person ID, etc). Same storage/validation as
    auction documents (private_uploads/, image or PDF, 10 MB cap) but
    profile-scoped since a seller may not have any auctions yet."""
    result = await db.execute(select(SellerProfile).where(SellerProfile.user_id == current_user.id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Apply as a seller before uploading a verification document")

    ext = ALLOWED_DOCUMENT_TYPES.get(file.content_type)
    if not ext:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: {', '.join(ALLOWED_DOCUMENT_TYPES)}",
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10 MB.")

    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(PRIVATE_UPLOAD_DIR, filename), "wb") as f:
        f.write(content)

    profile.verification_document = filename
    await db.commit()
    await db.refresh(profile)
    return profile


@sellers_router.get("/{profile_id}/verification-document")
async def download_verification_document(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Secure download - only the profile's own owner or staff (never a
    public URL), same authorization shape as the auction document endpoint."""
    result = await db.execute(select(SellerProfile).where(SellerProfile.id == profile_id))
    profile = result.scalars().first()
    if not profile or not profile.verification_document:
        raise HTTPException(status_code=404, detail="No verification document on file")

    is_staff = current_user.role.value in ("admin", "super_admin", "support")
    if not is_staff and current_user.id != profile.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")

    filepath = os.path.join(PRIVATE_UPLOAD_DIR, profile.verification_document)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(filepath, filename=os.path.basename(filepath))
