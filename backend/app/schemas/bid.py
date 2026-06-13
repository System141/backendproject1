from pydantic import BaseModel, Field
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

    class Config:
        from_attributes = True


class BidHistoryResponse(BaseModel):
    bids: list[BidResponse]
    total_count: int