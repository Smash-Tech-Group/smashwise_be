"""
api/v1/models/product.py

Product, ProductImage, and ProductReview models.

Product stores core product data including JSON fields for flexible
attributes (specifications, sizes, colors, delivery_info).

ProductReview is linked to both a product and a user, with a verified flag
for purchase-verified reviews.
"""

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, Text, ForeignKey,
    JSON, Numeric, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from api.v1.models.base_model import BaseTableModel


class Product(BaseTableModel):
    __tablename__ = "products"

    name           = Column(String(500), nullable=False)
    description    = Column(Text, nullable=True)
    price          = Column(Numeric(10, 2), nullable=False)
    old_price      = Column(Numeric(10, 2), nullable=True)
    badge          = Column(String(50), nullable=True)        # "NEW", "25% OFF", etc.
    stock_status   = Column(String(20), nullable=False, default="in_stock")  # in_stock | out_of_stock
    rating         = Column(Float, nullable=False, default=0.0)
    review_count   = Column(Integer, nullable=False, default=0)
    category       = Column(String(100), nullable=True)
    vendor         = Column(String(200), nullable=True)
    specifications = Column(JSON, nullable=True)              # { "Brand": "...", ... }
    sizes          = Column(JSON, nullable=True)              # [40, 42, 44, 47]
    colors         = Column(JSON, nullable=True)              # [{ "name": "Black", "hex": "#1a1a1a" }]
    delivery_info  = Column(JSON, nullable=True)              # { "delivery": "...", "return_policy": "..." }

    images  = relationship("ProductImage",  back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")


class ProductImage(BaseTableModel):
    __tablename__ = "product_images"

    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    url        = Column(String(1000), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="images")


class ProductReview(BaseTableModel):
    __tablename__ = "product_reviews"

    product_id    = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    user_id       = Column(String, ForeignKey("users.id"),    nullable=True, index=True)
    reviewer_name = Column(String(200), nullable=False)
    rating        = Column(Integer, nullable=False)  # 1-5
    comment       = Column(Text, nullable=True)
    verified      = Column(Boolean, default=False)

    product = relationship("Product", back_populates="reviews")
    user    = relationship("User",    backref="reviews")
