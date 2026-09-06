import asyncio
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.database import get_db
from app.models.domain import User, Auction, AuctionImage, PUBLIC_AUCTION_STATUSES
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
MAX_BATCH_FILES = 10
MAX_BATCH_CONTENT = 50 * 1024 * 1024
MAX_CSV_CONTENT = 2 * 1024 * 1024
thumbnail_slots = asyncio.Semaphore(2)


def _thumbnail(filepath: str) -> str:
    source = Path(filepath)
    target = source.parent / ".thumbnails" / (source.name + ".webp")
    if target.is_file() and target.stat().st_mtime_ns >= source.stat().st_mtime_ns:
        return str(target)
    target.parent.mkdir(exist_ok=True)
    temporary = target.with_name(uuid.uuid4().hex + ".part")
    try:
        with Image.open(source) as image:
            if image.width * image.height > 20_000_000:
                raise ValueError("Image dimensions too large for a thumbnail")
            image.thumbnail((320, 240))
            thumbnail = ImageOps.exif_transpose(image)
            thumbnail.save(temporary, format="WEBP", quality=75)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return str(target)

# Upload directory (local storage for MVP) - publicly servable via the
# `/uploads` static mount in main.py.
UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _copy_upload_file(source, filepath: str, max_size: int) -> int:
    """Copy a parsed upload in bounded chunks and publish it atomically."""
    temporary = f"{filepath}.part"
    total = 0
    try:
        with open(temporary, "wb") as target:
            while chunk := source.read(64 * 1024):
                total += len(chunk)
                if total > max_size:
                    raise ValueError("file too large")
                target.write(chunk)
        os.replace(temporary, filepath)
        return total
    except Exception:
        try:
            os.remove(temporary)
        except FileNotFoundError:
            pass
        raise


def _remove_file(filepath: str) -> None:
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass
    source = Path(filepath)
    (source.parent / ".thumbnails" / (source.name + ".webp")).unlink(missing_ok=True)


def _safe_storage_path(storage_ref: str, root: str) -> str:
    """Resolve a flat storage key and reject path traversal or absolute paths."""
    name = os.path.basename(storage_ref or "")
    if not name or (storage_ref != name and storage_ref != f"/uploads/{name}"):
        raise ValueError("invalid storage reference")
    root_path = Path(root).resolve()
    candidate = (root_path / name).resolve()
    if candidate.parent != root_path:
        raise ValueError("invalid storage reference")
    return str(candidate)

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
    auction_id: str = Query(...),
    sort_order: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an image file associated with the owner's auction.
    Only the auction owner (seller) can upload images to their auction.
    """
    auction = await _get_owned_auction_or_404(db, auction_id, current_user)

    # Validate file type
    ext = ALLOWED_TYPES.get(file.content_type)
    if not ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Allowed: {', '.join(ALLOWED_TYPES)}",
        )

    # Generate unique filename — ext from validated MIME type, never from filename
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save to disk (off the event loop - sync file I/O would otherwise
    # stall every other request on this single-process app, CLAUDE.md)
    try:
        await asyncio.to_thread(_copy_upload_file, file.file, filepath, MAX_FILE_SIZE)
    except ValueError:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    img_record = AuctionImage(
        id=str(uuid.uuid4()), auction_id=auction.id, image_url=f"/uploads/{filename}", sort_order=sort_order,
    )
    db.add(img_record)
    try:
        await db.commit()
        await db.refresh(img_record)
    except Exception:
        await db.rollback()
        await asyncio.to_thread(_remove_file, filepath)
        raise
    return build_auction_image_response(img_record)


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

    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(status_code=413, detail=f"A maximum of {MAX_BATCH_FILES} files is allowed")
    if any(ALLOWED_TYPES.get(file.content_type) is None for file in files):
        raise HTTPException(status_code=400, detail="All files must be JPEG, PNG, or WebP")

    saved_images = []
    saved_paths = []
    total_size = 0
    for sort_idx, file in enumerate(files):
        # Validate file type
        ext = ALLOWED_TYPES[file.content_type]

        # ext from validated MIME type, never from filename
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Save to disk in bounded chunks (off the event loop).
        try:
            size = await asyncio.to_thread(_copy_upload_file, file.file, filepath, MAX_FILE_SIZE)
        except ValueError:
            for path in saved_paths:
                await asyncio.to_thread(_remove_file, path)
            await db.rollback()
            raise HTTPException(status_code=413, detail="Each file may be at most 10 MB")
        except Exception:
            for path in saved_paths:
                await asyncio.to_thread(_remove_file, path)
            await db.rollback()
            raise
        total_size += size
        if total_size > MAX_BATCH_CONTENT:
            for path in saved_paths + [filepath]:
                await asyncio.to_thread(_remove_file, path)
            await db.rollback()
            raise HTTPException(status_code=413, detail="Total upload content may be at most 50 MB")
        saved_paths.append(filepath)

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

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        for path in saved_paths:
            await asyncio.to_thread(_remove_file, path)
        raise

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

    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(status_code=413, detail=f"A maximum of {MAX_BATCH_FILES} files is allowed")

    # Validate every file up front - fail the whole batch on the first bad
    # file rather than partially saving some and rejecting others.
    extensions = []
    for file in files:
        ext = ALLOWED_DOCUMENT_TYPES.get(file.content_type)
        if not ext:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for '{file.filename}': {file.content_type}. Allowed: {', '.join(ALLOWED_DOCUMENT_TYPES)}",
            )
        extensions.append(ext)

    saved_images = []
    saved_paths = []
    total_size = 0
    try:
      for sort_idx, (file, ext) in enumerate(zip(files, extensions)):
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(PRIVATE_UPLOAD_DIR, filename)
        try:
            size = await asyncio.to_thread(_copy_upload_file, file.file, filepath, MAX_FILE_SIZE)
        except ValueError:
            raise HTTPException(status_code=413, detail=f"'{file.filename}' is too large. Maximum size is 10 MB.")
        saved_paths.append(filepath)
        total_size += size
        if total_size > MAX_BATCH_CONTENT:
            raise HTTPException(status_code=413, detail="Total upload content may be at most 50 MB")

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
    except Exception:
        await db.rollback()
        for path in saved_paths:
            await asyncio.to_thread(_remove_file, path)
        raise
    for img in saved_images:
        await db.refresh(img)

    return [build_auction_image_response(img) for img in saved_images]


@uploads_router.get("/{image_id}/download")
async def download_file(
    image_id: str,
    thumbnail: bool = False,
    db: AsyncSession = Depends(get_db),
    viewer: dict | None = Depends(get_current_user_optional),
):
    """Doc §6.2's "güvenli indirme" (secure download): the only way to fetch
    a document's bytes. Public documents are open to anyone (same as images);
    private ones require the auction's own seller or staff/admin."""
    result = await db.execute(select(AuctionImage).where(AuctionImage.id == image_id))
    img = result.scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Media not found")

    auction_result = await db.execute(select(Auction).where(Auction.id == img.auction_id))
    auction = auction_result.scalars().first()
    is_staff = viewer is not None and viewer.get("role") in ("admin", "super_admin", "support")
    is_owner = auction is not None and viewer is not None and viewer.get("sub") == auction.seller_id
    if auction is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if auction.status not in PUBLIC_AUCTION_STATUSES and not (is_staff or is_owner):
        raise HTTPException(status_code=404, detail="Document not found")
    if img.visibility == "private":
        if viewer is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        if not (is_staff or is_owner):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this document")

    root = PRIVATE_UPLOAD_DIR if img.media_type == "document" else UPLOAD_DIR
    try:
        filepath = _safe_storage_path(img.image_url, root)
    except ValueError:
        raise HTTPException(status_code=404, detail="Media not found")
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Media missing on disk")
    if thumbnail:
        if img.media_type != "image":
            raise HTTPException(status_code=400, detail="Thumbnails are available for images only")
        async with thumbnail_slots:
            try:
                filepath = await asyncio.to_thread(_thumbnail, filepath)
            except (ValueError, UnidentifiedImageError, Image.DecompressionBombError):
                raise HTTPException(status_code=400, detail="Cannot create thumbnail for this image")
    headers = {"Cache-Control": "private, no-store"} if img.visibility == "private" else {}
    return FileResponse(filepath, filename=os.path.basename(filepath), headers=headers)
