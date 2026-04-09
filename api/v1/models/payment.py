"""
api/v1/models/payment.py

Payment model — one Payment record per Order.

status lifecycle:
    pending → paid
    pending → failed

tx_reference is populated when Paystack authorization_url is obtained.
metadata stores the raw Paystack response for audit purposes.
"""

from sqlalchemy import Column, String, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship

from api.v1.models.base_model import BaseTableModel

PAYMENT_STATUSES = {"pending", "paid", "failed"}


class Payment(BaseTableModel):
    __tablename__ = "payments"

    order_id          = Column(String,        ForeignKey("orders.id"), nullable=False, unique=True, index=True)
    amount            = Column(Numeric(10, 2), nullable=False)
    status            = Column(String,        nullable=False, default="pending")
    provider          = Column(String,        nullable=False, default="paystack")
    tx_reference      = Column(String,        nullable=True,  unique=True, index=True)
    authorization_url = Column(String,        nullable=True)
    payment_metadata  = Column(JSON,          nullable=True)   # raw Paystack response

    order = relationship("Order", back_populates="payment")