"""
api/v1/schemas/product.py

Pydantic schemas for Product, ProductImage, and ProductReview endpoints.
Extended to include review submission schema (ReviewSubmit) with
order_line_item_id, title, and media_urls fields.
"""

# File: api/v1/schemas/product.py

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
    """Legacy schema — used by existing POST /products/{id}/reviews route."""
    rating:  int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

    model_config = {"str_strip_whitespace": True}


class ReviewSubmit(BaseModel):
    """
    Schema for the new POST /api/v1/reviews endpoint.
    Tied to a specific order line item for deduplication.
    """
    order_line_item_id: str
    product_id:         str
    rating:             int = Field(..., ge=1, le=5)
    title:              str = Field(..., min_length=1, max_length=300)
    body:               Optional[str] = None
    reviewer_name:      str = Field(..., min_length=1, max_length=200)
    media_urls:         Optional[List[str]] = []

    model_config = {"str_strip_whitespace": True}


class ReviewOut(BaseModel):
    id:                 str
    product_id:         str
    user_id:            Optional[str]
    order_line_item_id: Optional[str]
    reviewer_name:      str
    title:              str
    rating:             int
    comment:            Optional[str]
    media_urls:         Optional[List[str]]
    verified:           bool
    created_at:         datetime

    model_config = {"from_attributes": True}


class CanReviewOut(BaseModel):
    can_review: bool


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
    images:         Optional[List[str]] = None

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
    image:        Optional[str] = None

    model_config = {"from_attributes": True}