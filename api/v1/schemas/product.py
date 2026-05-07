"""
api/v1/schemas/product.py

Pydantic schemas for Product, ProductImage, and ProductReview endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal


# ── Product Image ──────────────────────────────────────────────

class ProductImageOut(BaseModel):
    id:         str
    url:        str
    sort_order: int

    model_config = {"from_attributes": True}


# ── Product Review ─────────────────────────────────────────────

class ReviewCreate(BaseModel):
    rating:  int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

    model_config = {"str_strip_whitespace": True}


class ReviewOut(BaseModel):
    id:            str
    product_id:    str
    user_id:       Optional[str]
    reviewer_name: str
    rating:        int
    comment:       Optional[str]
    verified:      bool
    created_at:    datetime

    model_config = {"from_attributes": True}


# ── Rating Breakdown ───────────────────────────────────────────

class RatingBreakdownOut(BaseModel):
    """Count of reviews per star rating."""
    star_5: int = 0
    star_4: int = 0
    star_3: int = 0
    star_2: int = 0
    star_1: int = 0


# ── Product ────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name:           str = Field(..., min_length=1, max_length=500)
    description:    Optional[str] = None
    price:          Decimal = Field(..., gt=0)
    old_price:      Optional[Decimal] = None
    badge:          Optional[str] = None
    stock_status:   str = Field(default="in_stock", pattern="^(in_stock|out_of_stock)$")
    category:       Optional[str] = None
    vendor:         Optional[str] = None
    specifications: Optional[dict] = None
    sizes:          Optional[list] = None
    colors:         Optional[list] = None
    delivery_info:  Optional[dict] = None
    images:         Optional[List[str]] = None  # list of image URLs

    model_config = {"str_strip_whitespace": True}


class ProductUpdate(BaseModel):
    name:           Optional[str] = Field(None, min_length=1, max_length=500)
    description:    Optional[str] = None
    price:          Optional[Decimal] = None
    old_price:      Optional[Decimal] = None
    badge:          Optional[str] = None
    stock_status:   Optional[str] = Field(None, pattern="^(in_stock|out_of_stock)$")
    category:       Optional[str] = None
    vendor:         Optional[str] = None
    specifications: Optional[dict] = None
    sizes:          Optional[list] = None
    colors:         Optional[list] = None
    delivery_info:  Optional[dict] = None

    model_config = {"str_strip_whitespace": True}


class ProductOut(BaseModel):
    id:             str
    name:           str
    description:    Optional[str]
    price:          Decimal
    old_price:      Optional[Decimal]
    badge:          Optional[str]
    stock_status:   str
    rating:         float
    review_count:   int
    category:       Optional[str]
    vendor:         Optional[str]
    specifications: Optional[Any]
    sizes:          Optional[Any]
    colors:         Optional[Any]
    delivery_info:  Optional[Any]
    images:         List[ProductImageOut]
    created_at:     datetime
    updated_at:     datetime

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    """Lightweight product for listing / cards."""
    id:           str
    name:         str
    price:        Decimal
    old_price:    Optional[Decimal]
    badge:        Optional[str]
    stock_status: str
    rating:       float
    review_count: int
    category:     Optional[str]
    vendor:       Optional[str]
    image:        Optional[str] = None   # first image URL

    model_config = {"from_attributes": True}
