"""
api/v1/schemas/order.py

Pydantic schemas for Order / Checkout request and response.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class CheckoutRequest(BaseModel):
    """Body sent to POST /orders/checkout"""
    address_id:      Optional[str] = None     # null → no delivery address (pickup)
    delivery_method: str           = Field(..., pattern="^(home|pickup)$")
    promo_code:      Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """Body sent to PATCH /orders/{order_id}/status"""
    status: str = Field(..., pattern="^(processing|completed|cancelled)$")


class PromoApplyRequest(BaseModel):
    """Body sent to POST /orders/apply-promo"""
    code: str = Field(..., min_length=1, max_length=50)

    model_config = {"str_strip_whitespace": True}


class PromoApplyOut(BaseModel):
    code:     str
    discount: Decimal
    label:    str


class OrderItemOut(BaseModel):
    id:            str
    product_id:    str
    product_name:  str
    product_image: Optional[str]
    unit_price:    Decimal
    quantity:      int
    subtotal:      Decimal

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id:              str
    user_id:         str
    address_id:      Optional[str]
    delivery_method: str
    status:          str
    subtotal:        Decimal
    delivery_fee:    Decimal
    tax:             Decimal
    promo_discount:  Decimal
    total:           Decimal
    promo_code:      Optional[str]
    items:           List[OrderItemOut]
    created_at:      datetime
    updated_at:      datetime

    model_config = {"from_attributes": True}