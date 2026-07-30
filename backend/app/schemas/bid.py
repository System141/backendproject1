from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class BidCreateRequest(BaseModel):
    amount: float = Field(..., gt=0)
    idempotency_key: Optional[str] = Field(None, max_length=100)


class BidResponse(BaseModel):
    id: str
    auction_id: str
    user_id: str
    amount: float
    created_at: datetime
    user_name: str | None = None
    auction_title: str | None = None
    auction_current_price: float | None = None
    auction_status: str | None = None
    auction_end_time: datetime | None = None
    auction_lot_code: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BidHistoryResponse(BaseModel):
    bids: list[BidResponse]
    total_count: int
    current_price: float | None = None
    auction_status: str | None = None
    min_increment: float | None = None


class JoinAuctionResponse(BaseModel):
    auction_id: str
    user_id: str
    credits_spent: float
    joined_at: datetime
    already_joined: bool

    model_config = ConfigDict(from_attributes=True)


class JoinedAuctionResponse(BaseModel):
    """Doc §10.4 Joined Auctions: join date, credits spent, auction status, my bid status."""
    auction_id: str
    auction_title: str
    auction_status: str
    credits_spent: float
    joined_at: datetime
    my_bid_status: str  # "highest" | "outbid" | "no_bid"
