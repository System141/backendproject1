from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class SupportTicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)


class SupportTicketUpdateRequest(BaseModel):
    status: str = Field(..., pattern=r"^(open|in_progress|resolved|closed)$")


class SupportTicketResponse(BaseModel):
    id: str
    user_id: str
    subject: str
    message: str
    status: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)