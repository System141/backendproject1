from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


# ---------- Credit packages ----------
class CreditPackageResponse(BaseModel):
    id: str
    name: str
    credits: float
    price_eur: float
    active: bool
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class CreditPackageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    credits: float = Field(..., gt=0)
    price_eur: float = Field(..., gt=0)
    active: bool = True
    sort_order: int = 0


class CreditPackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    credits: Optional[float] = Field(None, gt=0)
    price_eur: Optional[float] = Field(None, gt=0)
    active: Optional[bool] = None
    sort_order: Optional[int] = None


# ---------- Bid increment rules ----------
class BidIncrementRuleResponse(BaseModel):
    id: int
    min_price: float
    increment: float
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class BidIncrementRuleCreate(BaseModel):
    min_price: float = Field(..., ge=0)
    increment: float = Field(..., gt=0)
    sort_order: int = 0


class BidIncrementRuleUpdate(BaseModel):
    min_price: Optional[float] = Field(None, ge=0)
    increment: Optional[float] = Field(None, gt=0)
    sort_order: Optional[int] = None


# ---------- Platform settings ----------
class PlatformSettingsResponse(BaseModel):
    anti_sniping_window_seconds: int
    anti_sniping_extension_seconds: int
    default_participation_credit_cost: float

    model_config = ConfigDict(from_attributes=True)


class PlatformSettingsUpdate(BaseModel):
    anti_sniping_window_seconds: Optional[int] = Field(None, ge=0)
    anti_sniping_extension_seconds: Optional[int] = Field(None, ge=0)
    default_participation_credit_cost: Optional[float] = Field(None, ge=0)


# ---------- Credit adjustments ----------
class CreditAdjustRequest(BaseModel):
    user_id: str
    amount: float  # +/- delta
    reason: str = Field(..., min_length=1, max_length=1000)


class CreditLedgerEntryResponse(BaseModel):
    id: str
    user_id: str
    type: str
    amount: float
    reference: Optional[str] = None
    balance_before: float
    balance_after: float
    actor_id: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Bid invalidate / auction cancel ----------
class ReasonRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)
