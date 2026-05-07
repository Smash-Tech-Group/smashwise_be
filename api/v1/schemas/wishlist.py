"""
api/v1/schemas/wishlist.py

Pydantic schemas for Wishlist endpoints.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class WishlistItemAdd(BaseModel):
    product_id: str


class WishlistItemOut(BaseModel):
    id:         str
    user_id:    str
    product_id: str
    created_at: datetime

    # Embedded product info (populated by the service layer)
    product_name:  Optional[str] = None
    product_price: Optional[Decimal] = None
    product_image: Optional[str] = None

    model_config = {"from_attributes": True}


class WishlistCheckOut(BaseModel):
    in_wishlist: bool
