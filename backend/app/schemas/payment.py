from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentCreateRequest(BaseModel):
    auction_id: str
    stripe_session_id: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    auction_id: str
    buyer_id: str
    amount: float
    status: str
    stripe_session_id: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class CommissionResponse(BaseModel):
    id: str
    auction_id: str
    seller_id: str
    amount: float
    rate: float
    status: str
    created_at: str

    class Config:
        from_attributes = True