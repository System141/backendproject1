from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class BidCreateRequest(BaseModel):
    amount: float = Field(..., gt=0)


class BidResponse(BaseModel):
    id: str
    auction_id: str
    user_id: str
    amount: float
    created_at: datetime
    user_name: str | None = None
    auction_title: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BidHistoryResponse(BaseModel):
    bids: list[BidResponse]
    total_count: int
    current_price: float | None = None
    auction_status: str | None = None
    min_increment: float | None = None
