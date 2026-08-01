import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, String, Float, Integer, ForeignKey, DateTime, Enum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
import enum

from .base import Base


class UserRole(str, enum.Enum):
    """Doc §17.1: Super Admin / Admin / Support tiers. `admin` and
    `super_admin` are equivalent in capability today (the doc doesn't
    specify anything super_admin-exclusive beyond "has everything") -
    `support` is the deliberately-restricted tier: it can access read-only/
    ticket-handling endpoints (get_current_staff) but NOT financial/credit/
    bid mutations (get_current_admin), by default-deny rather than needing
    every sensitive endpoint to explicitly exclude it."""
    buyer = "buyer"
    seller = "seller"
    corporate_seller = "corporate_seller"
    admin = "admin"
    super_admin = "super_admin"
    support = "support"


class AuctionStatus(str, enum.Enum):
    """Doc §12.1. DRAFT is reserved for the multi-step listing wizard
    (not yet wired to any endpoint). ENDED means bidding closed only -
    never implies a completed sale (doc §12: no Sold/Paid states in v1)."""
    draft = "draft"
    under_review = "under_review"
    upcoming = "upcoming"
    live = "live"
    extended = "extended"
    ended = "ended"
    cancelled = "cancelled"


# Statuses in which an auction is open for join/bid (live bidding window)
BIDDABLE_STATUSES = (AuctionStatus.live, AuctionStatus.extended)


def generate_uuid():
    return str(uuid.uuid4())


def _utcnow():
    # Naive UTC on purpose: every timestamp column here is a plain DateTime
    # (Postgres TIMESTAMP WITHOUT TIME ZONE). asyncpg rejects tz-aware
    # datetimes bound to that column type, so this must stay naive to work
    # against Postgres, not just SQLite (which is lenient either way).
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt):
    """Normalize a possibly tz-aware datetime to naive UTC before it's bound
    to a DateTime column or compared against one, so asyncpg doesn't reject it."""
    if dt is None or dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)
    preferred_language = Column(String, nullable=True)  # "me" or "en" (doc §10.6/§16.3); None = no preference set
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole, native_enum=False, length=50), default=UserRole.buyer)  # see AuctionStatus.status for why native_enum=False
    status = Column(String, default="active")
    accepted_terms = Column(Boolean, default=False, nullable=False)
    accepted_privacy = Column(Boolean, default=False, nullable=False)
    marketing_consent = Column(Boolean, default=False, nullable=False)
    reset_token_hash = Column(String, nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)  # doc §20 AC-01
    email_verification_token_hash = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    credits_balance = Column(Float, default=0.0)
    totp_secret = Column(String, nullable=True)  # doc §17.3: admin 2FA, base32 TOTP secret
    totp_enabled = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)

    seller_profile = relationship("SellerProfile", primaryjoin="User.id==SellerProfile.user_id", uselist=False, foreign_keys="SellerProfile.user_id", viewonly=True)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    status = Column(String, default="active")


class Auction(Base):
    __tablename__ = "auctions"

    id = Column(String, primary_key=True, default=generate_uuid)
    seller_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    start_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    min_increment = Column(Float, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    # native_enum=False: renders as VARCHAR, not a Postgres native enum type.
    # Postgres native enums need ALTER TYPE ... ADD VALUE to grow, which this
    # project's ADD-COLUMN-only migration system (migrations.py) can't do -
    # VARCHAR lets new AuctionStatus members ship as an ordinary code change.
    # length=50 is fixed and generous on purpose: SQLAlchemy otherwise sizes
    # the VARCHAR from whatever members exist when the table is first
    # created, and this same migration system has no ALTER COLUMN TYPE step
    # to widen it later if a longer member gets added.
    status = Column(Enum(AuctionStatus, native_enum=False, length=50), default=AuctionStatus.under_review, nullable=False)
    winner_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    is_featured = Column(Boolean, default=False)
    listing_fee = Column(Float, nullable=True)  # fee charged to seller for posting
    lot_code = Column(String, unique=True, nullable=True)
    participation_credit_cost = Column(Float, nullable=True)  # falls back to PlatformSettings.default_participation_credit_cost
    review_notes = Column(Text, nullable=True)  # admin's "changes requested" feedback (doc §11.5)
    contact_flagged = Column(Boolean, default=False, nullable=False)  # title/description looked like it leaks direct contact (doc §11.6)
    created_at = Column(DateTime, default=_utcnow)

    # Vehicle-specific fields (nullable)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    mileage = Column(Integer, nullable=True)
    fuel_type = Column(String, nullable=True)
    transmission = Column(String, nullable=True)
    damage_status = Column(String, nullable=True)

    # Doc §6.1: categorized known-defects section (vehicle detail). Kept
    # separate from damage_status (the free-text overall summary) so each
    # category can be shown/omitted independently on the detail page.
    defect_exterior = Column(String, nullable=True)
    defect_interior = Column(String, nullable=True)
    defect_mechanical = Column(String, nullable=True)
    defect_tyres = Column(String, nullable=True)
    defect_missing_parts = Column(String, nullable=True)

    # Equipment-specific fields (nullable). Doc §7.1: also uses
    # equipment_brand/serial_number/condition/location and the shared
    # model/year columns above - not repeated here.
    equipment_brand = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    location = Column(String, nullable=True)
    operating_hours = Column(Integer, nullable=True)
    engine_power = Column(String, nullable=True)
    operating_weight = Column(String, nullable=True)
    service_history = Column(Text, nullable=True)
    inspection_availability = Column(Boolean, nullable=True)

    # Shared between equipment (§7.1 "dimensions"/"accessories") and
    # commercial assets (§7.2.2 "dimensions"/"included items") - same
    # concept under each doc section's own naming.
    dimensions = Column(String, nullable=True)
    included_items = Column(Text, nullable=True)

    # Commercial-asset-specific (§7.2.2). Rest of that section's fields
    # (brand/model/year/condition/serials/location/known defects) reuse the
    # equipment/vehicle columns above - same concept, no need to duplicate.
    quantity = Column(Integer, nullable=True)

    # Relationships (for reference)
    seller = relationship("User", foreign_keys=[seller_id])
    winner = relationship("User", foreign_keys=[winner_user_id])
    images = relationship(
        "AuctionImage", back_populates="auction", cascade="all, delete-orphan"
    )


class Bid(Base):
    __tablename__ = "bids"

    id = Column(String, primary_key=True, default=generate_uuid)
    auction_id = Column(String, ForeignKey("auctions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    ip_address = Column(String)
    idempotency_key = Column(String, unique=True, nullable=True)
    invalidated = Column(Boolean, default=False, nullable=False)
    invalidated_reason = Column(Text, nullable=True)
    invalidated_by = Column(String, ForeignKey("users.id"), nullable=True)
    invalidated_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    auction = relationship("Auction", backref="bids")


class AuctionImage(Base):
    """Doc §18's "AuctionMedia" entity: real images/documents, type, order,
    visibility. Extends the existing AuctionImage table rather than adding a
    parallel one - CLAUDE.md/doc §18 explicitly allow adapting entity names
    to the project's existing naming."""
    __tablename__ = "auction_images"

    id = Column(String, primary_key=True, default=generate_uuid)
    auction_id = Column(String, ForeignKey("auctions.id"), nullable=False)
    image_url = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)
    media_type = Column(String, nullable=False, default="image")  # image | document
    visibility = Column(String, nullable=False, default="public")  # public | private (admin/seller only)
    # Doc §6.2: document category, only meaningful when media_type="document".
    doc_category = Column(String, nullable=True)  # registration | inspection | service | other

    auction = relationship("Auction", back_populates="images")


class AuctionParticipant(Base):
    """A user who has spent credits to join an auction (once, ever, per auction)."""
    __tablename__ = "auction_participants"

    id = Column(String, primary_key=True, default=generate_uuid)
    auction_id = Column(String, ForeignKey("auctions.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    credits_spent = Column(Float, nullable=False)
    joined_at = Column(DateTime, default=_utcnow)

    auction = relationship("Auction")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("auction_id", "user_id", name="uq_auction_participant"),
    )


class BidIncrementRule(Base):
    """Admin-managed minimum-bid-increment ranges, keyed by current price threshold."""
    __tablename__ = "bid_increment_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    min_price = Column(Float, nullable=False)
    increment = Column(Float, nullable=False)
    sort_order = Column(Integer, default=0)


class LotSequence(Base):
    """Per-prefix running counter used to generate unique, sequential Lot IDs."""
    __tablename__ = "lot_sequences"

    prefix = Column(String, primary_key=True)
    next_value = Column(Integer, nullable=False, default=1)


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


class CreditPurchase(Base):
    __tablename__ = "credit_purchases"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    credits_amount = Column(Float, nullable=False)
    amount_eur = Column(Float, nullable=False)
    stripe_session_id = Column(String, unique=True, nullable=True)
    status = Column(Enum(PaymentStatus, native_enum=False, length=50), default=PaymentStatus.pending)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", foreign_keys=[user_id])


class CreditPackage(Base):
    """Admin-managed credit packages shown in the credit store."""
    __tablename__ = "credit_packages"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    credits = Column(Float, nullable=False)
    price_eur = Column(Float, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)


class CreditLedgerType(str, enum.Enum):
    purchase = "purchase"
    join_spend = "join_spend"
    admin_adjust = "admin_adjust"
    reversal = "reversal"


class CreditLedger(Base):
    """Immutable ledger of every credit balance change. Never updated or deleted."""
    __tablename__ = "credit_ledger"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(CreditLedgerType, native_enum=False, length=50), nullable=False)
    amount = Column(Float, nullable=False)  # +/- delta
    reference = Column(String, nullable=True)  # auction id / purchase id / admin note id
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    actor_id = Column(String, ForeignKey("users.id"), nullable=True)  # admin who triggered adjust/reversal
    reason = Column(Text, nullable=True)  # required for admin_adjust / reversal
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])


class PlatformSettings(Base):
    """Single-row table (id=1) of admin-configurable bid engine settings."""
    __tablename__ = "platform_settings"

    id = Column(Integer, primary_key=True, default=1)
    anti_sniping_window_seconds = Column(Integer, nullable=False, default=120)
    anti_sniping_extension_seconds = Column(Integer, nullable=False, default=120)
    default_participation_credit_cost = Column(Float, nullable=False, default=10.0)


class NotificationType(str, enum.Enum):
    outbid = "outbid"
    bid_received = "bid_received"
    auction_won = "auction_won"
    auction_lost = "auction_lost"
    auction_ending_soon = "auction_ending_soon"
    auction_approved = "auction_approved"
    auction_rejected = "auction_rejected"
    auction_completed = "auction_completed"
    auction_cancelled = "auction_cancelled"
    seller_application_submitted = "seller_application_submitted"
    seller_verified = "seller_verified"
    seller_rejected = "seller_rejected"
    listing_changes_requested = "listing_changes_requested"
    auction_joined = "auction_joined"
    auction_extended = "auction_extended"
    credit_purchase_successful = "credit_purchase_successful"
    credit_purchase_failed = "credit_purchase_failed"
    system_alert = "system_alert"  # doc §19.7: bid-engine/payment-webhook/unhandled errors -> admin ops alert


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType, native_enum=False, length=50), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    auction_id = Column(String, ForeignKey("auctions.id"), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    # Doc §16.2: retried events (scheduler polls, gateway callbacks) must not
    # send duplicate notifications. Nullable so unrelated notifications don't
    # collide on NULL=NULL (Postgres/SQLite unique indexes allow many NULLs).
    event_key = Column(String, nullable=True, unique=True)

    user = relationship("User")
    auction = relationship("Auction")


class NotificationTemplate(Base):
    """Doc §17 admin panel checklist: 'Notification template management'.
    One row per (admin-customized) NotificationType. Only the types listed in
    TEMPLATABLE_NOTIFICATION_TYPES (app/services/notifications.py) are ever
    read at send-time - creating a row for any other type is a no-op, since
    the call site never passes template_vars for it."""
    __tablename__ = "notification_templates"

    type = Column(String, primary_key=True)  # matches NotificationType.value
    title_en = Column(Text, nullable=True)
    message_en = Column(Text, nullable=True)
    title_me = Column(Text, nullable=True)
    message_me = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    # Doc §14.2.2: fixed category so support can triage by topic; lot_code is
    # an optional free-text reference to the auction the ticket concerns.
    category = Column(String, nullable=False, default="other")
    lot_code = Column(String, nullable=True)
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")


class SellerVerificationStatus(str, enum.Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class SellerProfile(Base):
    """Doc §11.2/§11.3: seller application + verification status. One row per
    seller/corporate_seller user. Terms acceptance lives in TermsAcceptance
    (document_type="seller_terms"), not duplicated here."""
    __tablename__ = "seller_profiles"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    account_type = Column(String, nullable=False, default="individual")  # individual | company
    company_name = Column(String, nullable=True)
    pib = Column(String, nullable=True)  # PIB / registration number (company)
    authorized_person = Column(String, nullable=True)
    city = Column(String, nullable=True)  # registered/operating city in Montenegro
    seller_type = Column(String, nullable=True)  # dealer, rent-a-car, insurer, construction, individual, ...
    verification_status = Column(Enum(SellerVerificationStatus, native_enum=False, length=50), nullable=False, default=SellerVerificationStatus.pending)
    rejection_reason = Column(Text, nullable=True)
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class Watchlist(Base):
    """Doc §10.5: user's favorited/tracked auctions, synced across devices."""
    __tablename__ = "watchlist"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    auction_id = Column(String, ForeignKey("auctions.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")
    auction = relationship("Auction")

    __table_args__ = (
        UniqueConstraint("user_id", "auction_id", name="uq_watchlist_user_auction"),
    )


class TermsDocument(Base):
    """Doc §15: admin-managed legal document content, versioned. document_type
    is a free string (terms_of_use, auction_participation_rules, credit_terms,
    seller_terms, privacy_policy, cookie_policy, credit_refund_policy,
    legal_notice) - final legal text/routes are LITZOR's to supply (§21.1)."""
    __tablename__ = "terms_documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_type = Column(String, nullable=False)
    version = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint("document_type", "version", name="uq_terms_document_type_version"),
    )


class TermsAcceptance(Base):
    """Doc §15.1: audit trail of which terms version a user accepted, and when.
    Never updated or deleted - a re-consent is a new row."""
    __tablename__ = "terms_acceptances"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    document_type = Column(String, nullable=False)
    version = Column(String, nullable=False)
    accepted_at = Column(DateTime, default=_utcnow)
    ip_address = Column(String, nullable=True)

    user = relationship("User")
