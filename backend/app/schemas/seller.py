from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class SellerApplicationRequest(BaseModel):
    account_type: str = Field(..., pattern=r"^(individual|company)$")
    company_name: Optional[str] = Field(None, max_length=200)
    pib: Optional[str] = Field(None, max_length=50)
    authorized_person: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    seller_type: Optional[str] = Field(None, max_length=100)


class SellerProfileResponse(BaseModel):
    id: str
    user_id: str
    account_type: str
    company_name: Optional[str] = None
    pib: Optional[str] = None
    authorized_person: Optional[str] = None
    city: Optional[str] = None
    seller_type: Optional[str] = None
    verification_status: str
    rejection_reason: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
