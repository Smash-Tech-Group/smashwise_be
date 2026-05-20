"""
api/v1/schemas/subscription.py

Pydantic schemas for the newsletter subscription endpoint.

SubscriptionCreate  — request body for POST /newsletter/subscribe
SubscriptionOut     — response body (id + email + timestamps)

Email validation uses Pydantic's built-in EmailStr for RFC-5322 compliance.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr


class SubscriptionCreate(BaseModel):
    """Request body for POST /newsletter/subscribe."""

    email: EmailStr

    model_config = {"str_strip_whitespace": True}


class SubscriptionOut(BaseModel):
    """Returned on successful subscription."""

    id:         str
    email:      str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}