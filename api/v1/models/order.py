"""
api/v1/models/order.py

Order and OrderItem models.

Key design decisions:
  - unit_price is SNAPSHOTTED at checkout time so future price changes
    never corrupt historical order data.
  - All monetary columns use Numeric(10, 2) to avoid floating-point errors.
  - status transitions are validated in order_service.py, not at the DB level.

Status lifecycle:
    pending → processing → completed
    pending → cancelled
    processing → cancelled
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from api.v1.models.base_model import BaseTableModel

# Valid status values
ORDER_STATUSES = {"pending", "processing", "completed", "cancelled"}

# Allowed transitions  {from_status: {allowed_to_statuses}}
ORDER_TRANSITIONS: dict[str, set[str]] = {
    "pending":    {"processing", "cancelled"},
    "processing": {"completed", "cancelled"},
    "completed":  set(),          # terminal — no further transitions
    "cancelled":  set(),          # terminal — no further transitions
}


class Order(BaseTableModel):
    __tablename__ = "orders"

    user_id         = Column(String,        ForeignKey("users.id"),          nullable=False, index=True)
    address_id      = Column(String,        ForeignKey("user_addresses.id"), nullable=True)
    delivery_method = Column(String,        nullable=False)   # "home" | "pickup"
    status          = Column(String,        nullable=False,   default="pending")
    subtotal        = Column(Numeric(10, 2), nullable=False)
    delivery_fee    = Column(Numeric(10, 2), nullable=False)
    tax             = Column(Numeric(10, 2), nullable=False)
    promo_discount  = Column(Numeric(10, 2), nullable=False,  default=0)
    total           = Column(Numeric(10, 2), nullable=False)
    promo_code      = Column(String,        nullable=True)

    user    = relationship("User",        backref="orders")
    address = relationship("UserAddress", backref="orders")
    items   = relationship("OrderItem",   back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment",     back_populates="order", uselist=False)


class OrderItem(BaseTableModel):
    __tablename__ = "order_items"

    order_id      = Column(String,        ForeignKey("orders.id"), nullable=False, index=True)
    product_id    = Column(String,        nullable=False)
    product_name  = Column(String,        nullable=False)
    product_image = Column(String,        nullable=True)
    unit_price    = Column(Numeric(10, 2), nullable=False)   # snapshotted at checkout
    quantity      = Column(Integer,       nullable=False)
    subtotal      = Column(Numeric(10, 2), nullable=False)   # unit_price × quantity

    order = relationship("Order", back_populates="items")