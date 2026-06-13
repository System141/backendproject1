from pydantic import BaseModel, Field
from typing import Optional

class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    marketing_consent: Optional[bool] = None