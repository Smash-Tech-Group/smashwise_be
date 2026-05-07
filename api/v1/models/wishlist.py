"""
api/v1/models/wishlist.py

WishlistItem model — tracks products a user has saved to their wishlist.
A unique constraint on (user_id, product_id) prevents duplicate entries.
"""

from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from api.v1.models.base_model import BaseTableModel


class WishlistItem(BaseTableModel):
    __tablename__ = "wishlist_items"

    user_id    = Column(String, ForeignKey("users.id"),    nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )

    user    = relationship("User",    backref="wishlist_items")
    product = relationship("Product", backref="wishlist_items")
