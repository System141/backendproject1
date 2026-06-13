import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Float, Integer, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
import enum

from .base import Base


class UserRole(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    corporate_seller = "corporate_seller"
    admin = "admin"


class AuctionStatus(str, enum.Enum):
    pending_approval = "pending_approval"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.buyer)
    status = Column(String, default="active")
    accepted_terms = Column(Boolean, default=False, nullable=False)
    accepted_privacy = Column(Boolean, default=False, nullable=False)
    marketing_consent = Column(Boolean, default=False, nullable=False)
    reset_token_hash = Column(String, nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    status = Column(Enum(AuctionStatus), default=AuctionStatus.pending_approval)
    winner_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Vehicle-specific fields (nullable)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    mileage = Column(Integer, nullable=True)
    fuel_type = Column(String, nullable=True)
    transmission = Column(String, nullable=True)
    damage_status = Column(String, nullable=True)

    # Equipment-specific fields (nullable)
    equipment_brand = Column(String, nullable=True)
    serial_number = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    location = Column(String, nullable=True)

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
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)

    auction = relationship("Auction", backref="bids")


class AuctionImage(Base):
    __tablename__ = "auction_images"

    id = Column(String, primary_key=True, default=generate_uuid)
    auction_id = Column(String, ForeignKey("auctions.id"), nullable=False)
    image_url = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)

    auction = relationship("Auction", back_populates="images")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)