from pydantic import BaseModel
from typing import Optional


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    auction_id: Optional[str] = None
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True