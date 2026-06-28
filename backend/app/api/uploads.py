import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.domain import User, Auction, AuctionImage
from app.schemas.auction import AuctionImageResponse
from app.core.security import get_current_user

uploads_router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Allowed MIME types → safe extensions (never trust filename)
ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Upload directory (local storage for MVP)
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
        return AuctionImageResponse(
            id=img_record.id,
            image_url=img_record.image_url,
            sort_order=img_record.sort_order,
        )

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
    # Verify auction exists and user owns it
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

    return [
        AuctionImageResponse(
            id=img.id,
            image_url=img.image_url,
            sort_order=img.sort_order,
        )
        for img in saved_images
    ]
