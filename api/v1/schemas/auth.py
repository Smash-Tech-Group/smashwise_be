from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def _validate_email(value: str) -> str:
    value = value.strip().lower()
    if not _EMAIL_REGEX.match(value):
        raise ValueError("Invalid email address format.")
    return value


def _validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one number.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", value):
        raise ValueError("Password must contain at least one special character.")
    return value


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: str
    username: str = Field(..., min_length=2, max_length=50)
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password(v)


# ---------------------------------------------------------------------------
# OTP verification schemas
# ---------------------------------------------------------------------------

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("OTP must be a 6-digit numeric code.")
        return v


# ---------------------------------------------------------------------------
# Response / output schemas
# ---------------------------------------------------------------------------

class UserOut(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


# ---------------------------------------------------------------------------
# Legacy / stub schema kept for backward-compat with the /signin stub
# ---------------------------------------------------------------------------

class SignInRequest(BaseModel):
    """Schema for sign-in by phone (stub)."""
    phone_number: str = Field(..., min_length=10, max_length=20)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not re.match(r"^\+?[1-9]\d{1,14}$", v):
            raise ValueError("Invalid phone number format.")
        if not v.startswith("+"):
            if v.startswith("0"):
                v = "+234" + v[1:]
            elif len(v) == 10:
                v = "+234" + v
            else:
                v = "+" + v
        return v
