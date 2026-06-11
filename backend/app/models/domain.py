import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from .base import Base
import enum

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
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.buyer)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    status = Column(String, default="active")

class Auction(Base):
    __tablename__ = 'auctions'

    id = Column(String, primary_key=True, default=generate_uuid)
    seller_id = Column(String, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    start_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    min_increment = Column(Float, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(Enum(AuctionStatus), default=AuctionStatus.pending_approval)
    winner_user_id = Column(String, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Bid(Base):
    __tablename__ = 'bids'

    id = Column(String, primary_key=True, default=generate_uuid)
    auction_id = Column(String, ForeignKey('auctions.id'), nullable=False)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)

class AuctionImage(Base):
    __tablename__ = 'auction_images'

    id = Column(String, primary_key=True, default=generate_uuid)
    auction_id = Column(String, ForeignKey('auctions.id'), nullable=False)
    image_url = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
