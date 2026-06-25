from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ---------- Create ----------
class AuctionCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    category_id: int = Field(..., gt=0)
    start_price: float = Field(..., gt=0)
    min_increment: float = Field(..., gt=0)
    end_time: datetime = Field(...)

    # Vehicle fields (optional)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    mileage: Optional[int] = Field(None, ge=0)
    fuel_type: Optional[str] = Field(None, max_length=50)
    transmission: Optional[str] = Field(None, max_length=50)
    damage_status: Optional[str] = Field(None, max_length=200)

    # Equipment fields (optional)
    equipment_brand: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    condition: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)


# ---------- Update ----------
class AuctionUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    category_id: Optional[int] = Field(None, gt=0)
    start_price: Optional[float] = Field(None, gt=0)
    min_increment: Optional[float] = Field(None, gt=0)
    end_time: Optional[datetime] = None

    # Vehicle fields
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    mileage: Optional[int] = Field(None, ge=0)
    fuel_type: Optional[str] = Field(None, max_length=50)
    transmission: Optional[str] = Field(None, max_length=50)
    damage_status: Optional[str] = Field(None, max_length=200)

    # Equipment fields
    equipment_brand: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    condition: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)


# ---------- Image ----------
class AuctionImageResponse(BaseModel):
    id: str
    image_url: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


# ---------- Response ----------
class AuctionResponse(BaseModel):
    id: str
    seller_id: str
    category_id: int
    title: str
    description: str
    start_price: float
    current_price: float
    min_increment: float
    start_time: datetime
    end_time: datetime
    status: str
    winner_user_id: Optional[str] = None
    created_at: datetime

    # Vehicle fields
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    damage_status: Optional[str] = None

    # Equipment fields
    equipment_brand: Optional[str] = None
    serial_number: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------- Detail (with images + category info) ----------
class CategoryBrief(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class AuctionDetailResponse(AuctionResponse):
    images: list[AuctionImageResponse] = []
    category: Optional[CategoryBrief] = None


# ---------- Admin status update ----------
class AuctionStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(active|cancelled)$")