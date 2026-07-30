from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


_CATEGORY_PATTERN = r"^(account|credits_payment|auction_bid|seller_application|listing|technical_issue|other)$"


class SupportTicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    category: str = Field("other", pattern=_CATEGORY_PATTERN)
    lot_code: Optional[str] = Field(None, max_length=50)


class SupportTicketUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r"^(open|in_progress|resolved|closed)$")


class SupportTicketResponse(BaseModel):
    id: str
    user_id: str
    subject: str
    message: str
    category: str
    lot_code: str | None = None
    status: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)