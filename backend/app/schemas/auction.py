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
    # Doc §11.7: seller confirms listing authority/accuracy/known-defects
    # disclosure before submission. Server stores the acceptance timestamp
    # via TermsAcceptance (document_type="seller_listing_declaration").
    declaration_accepted: bool = Field(..., description="Seller confirms authority to list and accuracy of listing info")

    # Vehicle fields (optional)
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    mileage: Optional[int] = Field(None, ge=0)
    fuel_type: Optional[str] = Field(None, max_length=50)
    transmission: Optional[str] = Field(None, max_length=50)
    damage_status: Optional[str] = Field(None, max_length=200)
    defect_exterior: Optional[str] = Field(None, max_length=500)
    defect_interior: Optional[str] = Field(None, max_length=500)
    defect_mechanical: Optional[str] = Field(None, max_length=500)
    defect_tyres: Optional[str] = Field(None, max_length=500)
    defect_missing_parts: Optional[str] = Field(None, max_length=500)

    # Equipment fields (optional)
    equipment_brand: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    condition: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    operating_hours: Optional[int] = Field(None, ge=0)
    engine_power: Optional[str] = Field(None, max_length=100)
    operating_weight: Optional[str] = Field(None, max_length=100)
    service_history: Optional[str] = Field(None, max_length=2000)
    inspection_availability: Optional[bool] = None
    dimensions: Optional[str] = Field(None, max_length=200)
    included_items: Optional[str] = Field(None, max_length=2000)

    # Commercial-asset fields (optional)
    quantity: Optional[int] = Field(None, ge=0)


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
    defect_exterior: Optional[str] = Field(None, max_length=500)
    defect_interior: Optional[str] = Field(None, max_length=500)
    defect_mechanical: Optional[str] = Field(None, max_length=500)
    defect_tyres: Optional[str] = Field(None, max_length=500)
    defect_missing_parts: Optional[str] = Field(None, max_length=500)

    # Equipment fields
    equipment_brand: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    condition: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    operating_hours: Optional[int] = Field(None, ge=0)
    engine_power: Optional[str] = Field(None, max_length=100)
    operating_weight: Optional[str] = Field(None, max_length=100)
    service_history: Optional[str] = Field(None, max_length=2000)
    inspection_availability: Optional[bool] = None
    dimensions: Optional[str] = Field(None, max_length=200)
    included_items: Optional[str] = Field(None, max_length=2000)

    # Commercial-asset fields
    quantity: Optional[int] = Field(None, ge=0)


# ---------- Image ----------
class AuctionImageResponse(BaseModel):
    id: str
    image_url: str
    sort_order: int
    media_type: str = "image"
    doc_category: Optional[str] = None
    visibility: str = "public"

    model_config = ConfigDict(from_attributes=True)


# ---------- Response ----------
class AuctionResponse(BaseModel):
    id: str
    seller_id: str
    seller_name: Optional[str] = None
    seller_type: Optional[str] = None
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
    is_featured: bool = False
    lot_code: Optional[str] = None
    participation_credit_cost: Optional[float] = None
    review_notes: Optional[str] = None
    contact_flagged: bool = False
    created_at: datetime

    # Vehicle fields
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    mileage: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    damage_status: Optional[str] = None
    defect_exterior: Optional[str] = None
    defect_interior: Optional[str] = None
    defect_mechanical: Optional[str] = None
    defect_tyres: Optional[str] = None
    defect_missing_parts: Optional[str] = None

    # Equipment fields
    equipment_brand: Optional[str] = None
    serial_number: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    operating_hours: Optional[int] = None
    engine_power: Optional[str] = None
    operating_weight: Optional[str] = None
    service_history: Optional[str] = None
    inspection_availability: Optional[bool] = None
    dimensions: Optional[str] = None
    included_items: Optional[str] = None

    # Commercial-asset fields
    quantity: Optional[int] = None

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
    status: str = Field(..., pattern=r"^(live|cancelled)$")


# ---------- Post-close contact unlock (doc §12.5, §5.11 - AC-11/AC-12) ----------
class ContactInfoResponse(BaseModel):
    role: str  # "seller" or "winner" - whose contact this is
    name: str
    email: str
    phone: Optional[str] = None