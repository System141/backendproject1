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


class NotificationTemplateResponse(BaseModel):
    """Doc §17: admin panel 'Notification template management'."""
    type: str
    placeholders: list[str]
    title_en: Optional[str] = None
    message_en: Optional[str] = None
    title_me: Optional[str] = None
    message_me: Optional[str] = None


class NotificationTemplateUpdate(BaseModel):
    title_en: Optional[str] = None
    message_en: Optional[str] = None
    title_me: Optional[str] = None
    message_me: Optional[str] = None