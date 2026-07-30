from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TermsDocumentResponse(BaseModel):
    id: str
    document_type: str
    version: str
    content: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TermsDocumentCreate(BaseModel):
    document_type: str
    version: str
    content: str
    is_active: bool = True


class TermsAcceptanceCreate(BaseModel):
    document_type: str
    version: str


class TermsAcceptanceResponse(BaseModel):
    id: str
    document_type: str
    version: str
    accepted_at: datetime

    model_config = ConfigDict(from_attributes=True)
