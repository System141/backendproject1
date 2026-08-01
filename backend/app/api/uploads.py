import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.domain import User, Auction, AuctionImage
from app.schemas.auction import AuctionImageResponse
from app.core.security import get_current_user, get_current_user_optional
from app.services.auctions import build_auction_image_response

uploads_router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Allowed MIME types → safe extensions (never trust filename)
ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
# Doc §6.2: documents (registration/inspection/service/other) may be a PDF
# or a scanned image - reuses the same image MIME allowlist plus PDF.
ALLOWED_DOCUMENT_TYPES = {**ALLOWED_TYPES, "application/pdf": "pdf"}
DOCUMENT_CATEGORIES = {"registration", "inspection", "service", "other"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Upload directory (local storage for MVP) - publicly servable via the
# `/uploads` static mount in main.py.
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Doc §6.2: private documents must never be reachable by a guessed/reused
# direct URL, so they live outside the publicly-mounted UPLOAD_DIR entirely -
# every document (public or private) is served only through the authorizing
# /uploads/{id}/download endpoint below, never through the static mount.
PRIVATE_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "private_uploads"
)
os.makedirs(PRIVATE_UPLOAD_DIR, exist_ok=True)


async def _get_owned_auction_or_404(db: AsyncSession, auction_id: str, current_user: User) -> Auction:
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalars().first()
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    if auction.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only upload files to your own auctions")
    return auction


@uploads_router.post(
    "", response_model=AuctionImageResponse, status_code=status.HTTP_201_CREATED
)
async def upload_image(
    file: UploadFile = File(...),
    auction_id: str | None = None,
    sort_order: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an image file. Optionally associate with an auction_id.
    Only the auction owner (seller) can upload images to their auction.
    """
    # Validate file type
    ext = ALLOWED_TYPES.get(file.content_type)
    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10 MB.",
        )

    # If auction_id is provided, verify it exists and user owns it
    if auction_id:
        result = await db.execute(
            select(Auction).where(Auction.id == auction_id)
        )
        auction = result.scalars().first()
        if not auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        if auction.seller_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only upload images to your own auctions",
            )

    # Generate unique filename — ext from validated MIME type, never from filename
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save to disk
    with open(filepath, "wb") as f:
        f.write(content)

    image_url = f"/uploads/{filename}"

    # Save to database only if auction_id provided
    if auction_id:
        img_record = AuctionImage(
            id=str(uuid.uuid4()),
            auction_id=auction_id,
            image_url=image_url,
            sort_order=sort_order,
        )
        db.add(img_record)
        await db.commit()
        await db.refresh(img_record)
        return build_auction_image_response(img_record)

    # Return without database record (standalone upload)
    return AuctionImageResponse(
        id="",
        image_url=image_url,
        sort_order=sort_order,
    )


@uploads_router.post(
    "/batch",
    response_model=list[AuctionImageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_images_batch(
    files: list[UploadFile] = File(...),
    auction_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload multiple images at once and associate them with an auction.
    Only the auction owner (seller) can upload images to their auction.
    """
    auction = await _get_owned_auction_or_404(db, auction_id, current_user)

    saved_images = []
    for sort_idx, file in enumerate(files):
        # Validate file type
        ext = ALLOWED_TYPES.get(file.content_type)
        if not ext:
            continue  # Skip invalid files silently

        # Read file content
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            continue  # Skip oversized files silently

        # ext from validated MIME type, never from filename
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Save to disk
        with open(filepath, "wb") as f:
            f.write(content)

        image_url = f"/uploads/{filename}"

        # Save to database
        img_record = AuctionImage(
            id=str(uuid.uuid4()),
            auction_id=auction_id,
            image_url=image_url,
            sort_order=sort_idx,
        )
        db.add(img_record)
        saved_images.append(img_record)

    await db.commit()

    # Refresh all saved images
    for img in saved_images:
        await db.refresh(img)

    return [build_auction_image_response(img) for img in saved_images]


@uploads_router.post(
    "/documents",
    response_model=list[AuctionImageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents_batch(
    files: list[UploadFile] = File(...),
    auction_id: str = Query(...),
    doc_category: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Doc §6.2: seller uploads registration/inspection/service/other
    documents for their auction. Unlike the photo batch endpoint, an invalid
    file here is REJECTED (400), not silently skipped - a seller who uploads
    a rejected registration document needs to know it didn't save, rather
    than discovering a missing document later with no error ever shown."""
    if doc_category not in DOCUMENT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid doc_category: {doc_category}. Allowed: {', '.join(sorted(DOCUMENT_CATEGORIES))}",
        )
    auction = await _get_owned_auction_or_404(db, auction_id, current_user)

    # Validate every file up front - fail the whole batch on the first bad
    # file rather than partially saving some and rejecting others.
    contents = []
    for file in files:
        ext = ALLOWED_DOCUMENT_TYPES.get(file.content_type)
        if not ext:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for '{file.filename}': {file.content_type}. Allowed: {', '.join(ALLOWED_DOCUMENT_TYPES)}",
            )
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{file.filename}' is too large. Maximum size is 10 MB.",
            )
        contents.append((content, ext))

    saved_images = []
    for sort_idx, (content, ext) in enumerate(contents):
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(PRIVATE_UPLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(content)

        img_record = AuctionImage(
            id=str(uuid.uuid4()),
            auction_id=auction_id,
            image_url=filename,  # internal storage reference only - never served directly, see build_auction_image_response
            sort_order=sort_idx,
            media_type="document",
            doc_category=doc_category,
            visibility="private",  # doc §6.2: admin decides what becomes public, default to the safer choice
        )
        db.add(img_record)
        saved_images.append(img_record)

    await db.commit()
    for img in saved_images:
        await db.refresh(img)

    return [build_auction_image_response(img) for img in saved_images]


@uploads_router.get("/{image_id}/download")
async def download_file(
    image_id: str,
    db: AsyncSession = Depends(get_db),
    viewer: dict | None = Depends(get_current_user_optional),
):
    """Doc §6.2's "güvenli indirme" (secure download): the only way to fetch
    a document's bytes. Public documents are open to anyone (same as images);
    private ones require the auction's own seller or staff/admin."""
    result = await db.execute(select(AuctionImage).where(AuctionImage.id == image_id))
    img = result.scalars().first()
    if not img or img.media_type != "document":
        raise HTTPException(status_code=404, detail="Document not found")

    if img.visibility == "private":
        if viewer is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        auction_result = await db.execute(select(Auction).where(Auction.id == img.auction_id))
        auction = auction_result.scalars().first()
        is_staff = viewer.get("role") in ("admin", "super_admin", "support")
        is_owner = auction is not None and viewer.get("sub") == auction.seller_id
        if not (is_staff or is_owner):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this document")

    filepath = os.path.join(PRIVATE_UPLOAD_DIR, img.image_url)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(filepath, filename=os.path.basename(filepath))
