from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="buyer", pattern=r"^(buyer|seller|corporate_seller|admin)$")
    accepted_terms: bool = Field(default=False)
    accepted_privacy: bool = Field(default=False)
    marketing_consent: bool = Field(default=False)

class LoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = Field(None, max_length=10)  # doc §17.3: admin 2FA, required only once enabled

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"
    email_verification_token: Optional[str] = None  # dev-mode only, doc §20 AC-01 (see forgot-password's reset_token for the same pattern)

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=128)

class EmailVerifyRequest(BaseModel):
    token: str

class TotpSetupResponse(BaseModel):
    secret: str
    otpauth_url: str

class TotpCodeRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)

class TotpStatusResponse(BaseModel):
    enabled: bool

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    preferred_language: Optional[str] = None
    role: str
    status: str
    email_verified: bool = False
    created_at: str

    model_config = ConfigDict(from_attributes=True)