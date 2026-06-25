from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)