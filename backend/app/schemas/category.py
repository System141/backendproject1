from pydantic import BaseModel
from typing import Optional


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: Optional[int] = None
    status: str

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    slug: str
    parent_id: Optional[int] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    status: Optional[str] = None