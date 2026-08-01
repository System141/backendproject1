"""
Auction service: shared business logic used by both the REST endpoints and the scheduler.

Consolidates finalize logic, auction response building, and common helpers
so that API routers and the background scheduler call the same code.
"""
import re
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, desc, asc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.domain import (
    Auction, AuctionImage, AuctionStatus, Bid, User, NotificationType, BidIncrementRule, PlatformSettings,
    Category, LotSequence, TermsDocument,
)
from app.services.notifications import send_notification
from app.schemas.auction import AuctionResponse, AuctionImageResponse

logger = logging.getLogger("bidmont.auction_service")


def anonymize_bidder(auction_id: str, user_id: str) -> str:
    """
    Doc §5.8: bid history must show "Bidder #2817", never a real name, to
    protect other bidders' identity during a live auction. Deterministic
    per (auction, user) so the same bidder keeps the same number within one
    auction's history, without needing a new DB column.
    """
    digest = hashlib.sha256(f"{auction_id}:{user_id}".encode()).hexdigest()
    return f"Bidder #{int(digest[:8], 16) % 10000:04d}"


_PHONE_RE = re.compile(r"(?:\d[\s\-\(\)]*){6,}\d")  # 6+ digits, not 6+ chars including separators
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_URL_RE = re.compile(r"(https?://|www\.)\S+", re.IGNORECASE)


def looks_like_direct_contact(*texts: str) -> bool:
    """
    Doc §11.6: flag listings whose title/description try to bypass the
    credit model by sharing a phone/email/URL directly. Detection only -
    the doc asks for a visible admin-review warning, not an automatic hard
    block, since a false positive (e.g. a VIN-like number) shouldn't stop
    a legitimate listing.
    """
    blob = " ".join(t for t in texts if t)
    return bool(_PHONE_RE.search(blob) or _EMAIL_RE.search(blob) or _URL_RE.search(blob))


async def get_bid_increment(db: AsyncSession, current_price: float, fallback: float) -> float:
    """
    Admin-configured minimum bid increment for the given price, from the
    highest BidIncrementRule threshold at or below current_price. Falls back
    to the auction's own min_increment column until admin rules exist
    (bid-increment table values are one of the LITZOR-supplied inputs, §21.1).
    """
    result = await db.execute(
        select(BidIncrementRule)
        .where(BidIncrementRule.min_price <= current_price)
        .order_by(desc(BidIncrementRule.min_price))
        .limit(1)
    )
    rule = result.scalars().first()
    return rule.increment if rule else fallback


async def generate_lot_code(db: AsyncSession, category: Category) -> str:
    """
    Server-generated, unique, sequential Lot ID: BM-{PREFIX}-{seq:06d},
    e.g. BM-VEH-000128 (spec §5.3). Prefix comes from the category slug so
    it follows the admin-managed taxonomy instead of a hardcoded category
    list. Uses a locked per-prefix counter row, retrying if a concurrent
    request is creating that prefix's counter for the first time.
    """
    prefix = "".join(ch for ch in (category.slug or category.name or "").upper() if ch.isalnum())[:3] or "LOT"
    for _ in range(3):
        result = await db.execute(select(LotSequence).where(LotSequence.prefix == prefix).with_for_update())
        seq = result.scalars().first()
        if seq is None:
            try:
                # A SAVEPOINT (not a full session rollback) so a concurrent
                # insert of this same prefix's counter row only unwinds the
                # counter row, not every other ORM object (auction, category,
                # ...) the caller still needs to use after this returns.
                async with db.begin_nested():
                    db.add(LotSequence(prefix=prefix, next_value=1))
            except IntegrityError:
                continue
        result = await db.execute(select(LotSequence).where(LotSequence.prefix == prefix).with_for_update())
        seq = result.scalars().first()
        value = seq.next_value
        seq.next_value = value + 1
        await db.flush()
        return f"BM-{prefix}-{value:06d}"
    raise RuntimeError(f"Could not allocate lot code for prefix {prefix}")


async def get_or_create_settings(db: AsyncSession) -> PlatformSettings:
    """Fetch the single PlatformSettings row (id=1), creating it with defaults if absent."""
    result = await db.execute(select(PlatformSettings).where(PlatformSettings.id == 1))
    settings = result.scalars().first()
    if settings:
        return settings
    try:
        # SAVEPOINT: see generate_lot_code for why this isn't a full rollback.
        async with db.begin_nested():
            db.add(PlatformSettings(id=1))
    except IntegrityError:
        pass  # concurrent request already created it
    result = await db.execute(select(PlatformSettings).where(PlatformSettings.id == 1))
    return result.scalars().first()


SELLER_DECLARATION_TEXT = (
    "I confirm that I have the authority to list this asset, that the "
    "information and images provided are accurate, and that any known "
    "defects have been disclosed."
)
SELLER_DECLARATION_VERSION = "1.0"


async def get_or_create_seller_declaration(db: AsyncSession) -> TermsDocument:
    """
    Doc §11.7 requires the seller's pre-submit declaration acceptance to
    record a "terms version" - not just a bare string, so the audit trail
    can actually be traced back to what was agreed to. Unlike the
    LITZOR-authored legal documents in §15 (Terms of Use, Privacy Policy,
    ...), this declaration's wording is app copy, not counsel-approved
    legal text, so it's safe to auto-provision here rather than wait on an
    admin to publish it - same idempotent get-or-create shape as
    get_or_create_settings above.
    """
    result = await db.execute(
        select(TermsDocument).where(
            TermsDocument.document_type == "seller_listing_declaration",
            TermsDocument.is_active == True,  # noqa: E712
        )
    )
    doc = result.scalars().first()
    if doc:
        return doc
    try:
        async with db.begin_nested():
            db.add(TermsDocument(
                id=str(uuid.uuid4()),
                document_type="seller_listing_declaration",
                version=SELLER_DECLARATION_VERSION,
                content=SELLER_DECLARATION_TEXT,
                is_active=True,
            ))
    except IntegrityError:
        pass  # concurrent request already created it
    result = await db.execute(
        select(TermsDocument).where(
            TermsDocument.document_type == "seller_listing_declaration",
            TermsDocument.is_active == True,  # noqa: E712
        )
    )
    return result.scalars().first()


async def finalize_auction(
    db: AsyncSession,
    auction: Auction,
    broadcast: bool = True,
) -> dict:
    """
    Finalize an ended auction:
    - Determine the highest valid bidder (if any), tie-broken by earliest bid.
    - Mark auction as completed.
    - Notify seller, winner, and losing bidders.
    - Optionally broadcast via WebSocket.

    BidMont never creates a sale/payment record here - closing an auction
    only determines the highest bid/bidder; the actual sale happens directly
    between buyer and seller.

    Returns a summary dict.
    """
    # Find the highest valid bid; ties go to whichever was placed first.
    bid_result = await db.execute(
        select(Bid)
        .where(Bid.auction_id == auction.id, Bid.invalidated == False)  # noqa: E712
        .order_by(desc(Bid.amount), asc(Bid.created_at))
        .limit(1)
    )
    highest_bid = bid_result.scalars().first()

    winner_id = highest_bid.user_id if highest_bid else None

    auction.status = AuctionStatus.ended
    auction.winner_user_id = winner_id

    # Notify winner (BidMont never creates a sale/payment record - buyer and
    # seller settle directly per the platform-role boundary)
    if winner_id and highest_bid:
        winner_user = await db.execute(
            select(User).where(User.id == winner_id)
        )
        winner_user_obj = winner_user.scalars().first()
        if winner_user_obj:
            await send_notification(
                db, winner_id,
                NotificationType.auction_won,
                f"You won: {auction.title}",
                f"Congratulations! You won the auction '{auction.title}' with a bid of ${highest_bid.amount:.2f}.",
                auction_id=auction.id,
                send_email=True,
                event_key=f"auction_ended:{auction.id}:winner",
                title_me=f"Pobijedili ste: {auction.title}",
                message_me=f"Čestitamo! Pobijedili ste na aukciji '{auction.title}' sa ponudom od ${highest_bid.amount:.2f}.",
            )

    # Notify seller
    await send_notification(
        db, auction.seller_id,
        NotificationType.auction_completed,
        f"Auction completed: {auction.title}",
        f"Your auction '{auction.title}' has ended. Winner: {winner_id if winner_id else 'No bids'}.",
        auction_id=auction.id,
        send_email=True,
        event_key=f"auction_ended:{auction.id}:seller",
        title_me=f"Aukcija završena: {auction.title}",
        message_me=f"Vaša aukcija '{auction.title}' je završena. Pobjednik: {winner_id if winner_id else 'Nema ponuda'}.",
    )

    # Notify other bidders they lost
    if highest_bid:
        other_bidders_result = await db.execute(
            select(Bid.user_id)
            .where(
                Bid.auction_id == auction.id,
                Bid.user_id != winner_id,
            )
            .distinct()
        )
        other_bidder_ids = other_bidders_result.scalars().all()
        for loser_id in other_bidder_ids:
            await send_notification(
                db, loser_id,
                NotificationType.auction_lost,
                f"Auction ended: {auction.title}",
                f"The auction '{auction.title}' has ended. Another user won with a bid of ${highest_bid.amount:.2f}.",
                auction_id=auction.id,
                send_email=False,
                event_key=f"auction_ended:{auction.id}:loser:{loser_id}",
                title_me=f"Aukcija završena: {auction.title}",
                message_me=f"Aukcija '{auction.title}' je završena. Drugi korisnik je pobijedio sa ponudom od ${highest_bid.amount:.2f}.",
            )

    # Broadcast auction status change via WebSocket
    if broadcast:
        from app.api.ws import manager
        await manager.broadcast(auction.id, {
            "type": "auction_status_changed",
            "auction_id": auction.id,
            "status": "completed",
            "winner_user_id": winner_id,
            "winning_bid": highest_bid.amount if highest_bid else None,
        })

    await db.commit()

    logger.info(
        f"Finalized auction {auction.id} ('{auction.title}'). "
        f"Winner: {winner_id or 'None'}"
    )

    return {
        "status": "ended",  # bidding closed only - never implies a completed sale (doc §12)
        "auction_id": auction.id,
        "winner_user_id": winner_id,
        "winning_bid": highest_bid.amount if highest_bid else None,
        "has_bids": highest_bid is not None,
    }


def build_auction_response(auction: Auction) -> AuctionResponse:
    """Build an AuctionResponse from an Auction ORM instance."""
    return AuctionResponse(
        id=auction.id,
        seller_id=auction.seller_id,
        seller_name=auction.seller.name if hasattr(auction, 'seller') and auction.seller else None,
        seller_type=auction.seller.seller_profile.seller_type if hasattr(auction, 'seller') and auction.seller and auction.seller.seller_profile else None,
        category_id=auction.category_id,
        title=auction.title,
        description=auction.description,
        start_price=auction.start_price,
        current_price=auction.current_price,
        min_increment=auction.min_increment,
        start_time=auction.start_time,
        end_time=auction.end_time,
        status=auction.status.value,
        winner_user_id=auction.winner_user_id,
        is_featured=bool(auction.is_featured) if auction.is_featured is not None else False,
        lot_code=auction.lot_code,
        participation_credit_cost=auction.participation_credit_cost,
        review_notes=auction.review_notes,
        contact_flagged=bool(auction.contact_flagged),
        created_at=auction.created_at,
        brand=auction.brand,
        model=auction.model,
        year=auction.year,
        mileage=auction.mileage,
        fuel_type=auction.fuel_type,
        transmission=auction.transmission,
        damage_status=auction.damage_status,
        defect_exterior=auction.defect_exterior,
        defect_interior=auction.defect_interior,
        defect_mechanical=auction.defect_mechanical,
        defect_tyres=auction.defect_tyres,
        defect_missing_parts=auction.defect_missing_parts,
        equipment_brand=auction.equipment_brand,
        serial_number=auction.serial_number,
        condition=auction.condition,
        location=auction.location,
        operating_hours=auction.operating_hours,
        engine_power=auction.engine_power,
        operating_weight=auction.operating_weight,
        service_history=auction.service_history,
        inspection_availability=auction.inspection_availability,
        dimensions=auction.dimensions,
        included_items=auction.included_items,
        quantity=auction.quantity,
    )


def build_auction_image_response(img: AuctionImage) -> AuctionImageResponse:
    """Build an AuctionImageResponse from an AuctionImage ORM instance.

    Doc §6.2: documents need a secure, visibility-checked download - never a
    direct static-file URL (private ones would otherwise be reachable by
    anyone who guesses/reuses the filename). Images keep their existing
    directly-servable `/uploads/...` URL unchanged; only documents get their
    `image_url` rewritten to route through the authorizing download endpoint.
    """
    image_url = f"/api/uploads/{img.id}/download" if img.media_type == "document" else img.image_url
    return AuctionImageResponse(
        id=img.id, image_url=image_url, sort_order=img.sort_order,
        media_type=img.media_type, doc_category=img.doc_category, visibility=img.visibility,
    )


def visible_auction_images(auction: Auction, viewer_user_id: Optional[str], viewer_is_staff: bool) -> list[AuctionImage]:
    """Doc §6.2: private documents are visible only to the auction's own
    seller or staff/admin - everyone else (including anonymous visitors)
    only sees public images/documents. Images are always public today."""
    is_owner_or_staff = viewer_is_staff or (viewer_user_id is not None and viewer_user_id == auction.seller_id)
    return [
        img for img in (auction.images or [])
        if img.visibility == "public" or is_owner_or_staff
    ]