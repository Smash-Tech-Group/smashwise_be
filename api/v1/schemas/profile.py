"""
api/v1/schemas/profile.py

Pydantic schemas for the Profile endpoints.

ProfileOut   — response schema (GET and PATCH)
ProfileUpdate — request body for PATCH /profile (all fields optional)

Phone validation accepts:
  +234XXXXXXXXXX  (E.164 Nigerian format)
  0XXXXXXXXXX     (local Nigerian format, 11 digits)

Email is intentionally excluded from ProfileUpdate — it cannot be
changed via the profile endpoint.
"""

import re
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ── Nigerian phone regex ───────────────────────────────────────
# Accepts: +2348012345678  or  08012345678
_NG_PHONE_RE = re.compile(
    r"^(\+234[789][01]\d{8}|0[789][01]\d{8})$"
)


class ProfileOut(BaseModel):
    """Returned by GET /profile and PATCH /profile."""

    id:         str
    email:      str
    username:   str
    full_name:  Optional[str]
    phone:      Optional[str]
    avatar_url: Optional[str]
    is_active:  bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    """
    Request body for PATCH /profile.

    All fields are optional — only provided fields are updated.
    Passing null / None for a field does NOT overwrite existing data;
    that logic is enforced in profile_service.update_profile().
    """

    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="User display name (max 100 characters)",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Nigerian phone number: +234XXXXXXXXXX or 0XXXXXXXXXX",
    )

    model_config = {"str_strip_whitespace": True}

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalized = v.strip().replace(" ", "").replace("-", "")
        if not _NG_PHONE_RE.match(normalized):
            raise ValueError(
                "Invalid phone number format. "
                "Use +234XXXXXXXXXX or 0XXXXXXXXXX (Nigerian numbers only)."
            )
        return normalized