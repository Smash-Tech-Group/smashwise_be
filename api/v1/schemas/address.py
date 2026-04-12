"""
api/v1/schemas/address.py

Pydantic schemas for UserAddress request / response.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

VALID_CATEGORIES = {"home", "work", "gym", "church", "school", "custom"}


class AddressCreate(BaseModel):
    category:       str = Field(..., description="home | work | gym | church | school | custom")
    name:           str = Field(..., min_length=1, max_length=100)
    contact_person: str = Field(..., min_length=1, max_length=100)
    address:        str = Field(..., min_length=5, max_length=500)
    is_default:     bool = False

    model_config = {"str_strip_whitespace": True}

    def model_post_init(self, __context):
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}")


class AddressUpdate(BaseModel):
    category:       Optional[str]  = None
    name:           Optional[str]  = Field(None, min_length=1, max_length=100)
    contact_person: Optional[str]  = Field(None, min_length=1, max_length=100)
    address:        Optional[str]  = Field(None, min_length=5, max_length=500)
    is_default:     Optional[bool] = None

    model_config = {"str_strip_whitespace": True}

    def model_post_init(self, __context):
        if self.category is not None and self.category not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}")


class AddressOut(BaseModel):
    id:             str
    user_id:        str
    category:       str
    name:           str
    contact_person: str
    address:        str
    is_default:     bool
    created_at:     datetime
    updated_at:     datetime

    model_config = {"from_attributes": True}