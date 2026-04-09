"""
api/v1/schemas/payment.py

Pydantic schemas for Payment request / response and Paystack webhook.
"""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal


class PaymentOut(BaseModel):
    id:                str
    order_id:          str
    amount:            Decimal
    status:            str
    provider:          str
    tx_reference:      Optional[str]
    authorization_url: Optional[str]
    created_at:        datetime
    updated_at:        datetime

    model_config = {"from_attributes": True}


class PaymentInitOut(BaseModel):
    """Returned after a successful Paystack payment initialization."""
    authorization_url: str
    access_code:       str
    reference:         str
    payment:           PaymentOut


# ── Paystack webhook ───────────────────────────────────────────
class PaystackWebhookData(BaseModel):
    reference:  str
    status:     str           # "success" | "failed"
    amount:     int           # in kobo (divide by 100 for naira)
    metadata:   Optional[Any] = None


class PaystackWebhookPayload(BaseModel):
    event: str                # "charge.success" | "charge.failed"
    data:  PaystackWebhookData