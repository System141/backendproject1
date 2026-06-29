from pydantic import BaseModel, ConfigDict
from typing import Optional


class PaymentCreateRequest(BaseModel):
    auction_id: str
    payment_session_id: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    auction_id: str
    buyer_id: str
    amount: float
    buyer_service_fee: Optional[float] = None
    status: str
    payment_session_id: Optional[str] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class CommissionResponse(BaseModel):
    id: str
    auction_id: str
    seller_id: str
    amount: float
    rate: float
    status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)