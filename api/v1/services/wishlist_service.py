"""
api/v1/services/wishlist_service.py

Business logic for Wishlist CRUD.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.core.base.services import Service
from api.v1.models.wishlist import WishlistItem
from api.v1.models.product import Product
from api.v1.models.user import User


class WishlistService(Service):
    # ── Abstract stubs ─────────────────────────────────────────
    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    # ── Public methods ─────────────────────────────────────────

    def get_wishlist(self, db: Session, user: User) -> list[dict]:
        """Return all wishlist items for the user with embedded product info."""
        items = (
            db.query(WishlistItem)
            .filter(WishlistItem.user_id == user.id)
            .order_by(WishlistItem.created_at.desc())
            .all()
        )
        result = []
        for item in items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            first_image = None
            if product and product.images:
                sorted_imgs = sorted(product.images, key=lambda img: img.sort_order)
                first_image = sorted_imgs[0].url if sorted_imgs else None

            result.append({
                "id": item.id,
                "user_id": item.user_id,
                "product_id": item.product_id,
                "created_at": item.created_at,
                "product_name":  product.name  if product else None,
                "product_price": product.price if product else None,
                "product_image": first_image,
            })
        return result

    def add_to_wishlist(self, db: Session, user: User, product_id: str) -> dict:
        """Add a product to the user's wishlist."""
        # Verify product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        # Check if already in wishlist
        existing = (
            db.query(WishlistItem)
            .filter(
                WishlistItem.user_id == user.id,
                WishlistItem.product_id == product_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is already in your wishlist.",
            )

        item = WishlistItem(user_id=user.id, product_id=product_id)
        db.add(item)
        db.commit()
        db.refresh(item)

        first_image = None
        if product.images:
            sorted_imgs = sorted(product.images, key=lambda img: img.sort_order)
            first_image = sorted_imgs[0].url if sorted_imgs else None

        return {
            "id": item.id,
            "user_id": item.user_id,
            "product_id": item.product_id,
            "created_at": item.created_at,
            "product_name":  product.name,
            "product_price": product.price,
            "product_image": first_image,
        }

    def remove_from_wishlist(self, db: Session, user: User, product_id: str) -> None:
        """Remove a product from the user's wishlist."""
        item = (
            db.query(WishlistItem)
            .filter(
                WishlistItem.user_id == user.id,
                WishlistItem.product_id == product_id,
            )
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product is not in your wishlist.",
            )
        db.delete(item)
        db.commit()

    def check_wishlist(self, db: Session, user: User, product_id: str) -> bool:
        """Check if a product is in the user's wishlist."""
        exists = (
            db.query(WishlistItem)
            .filter(
                WishlistItem.user_id == user.id,
                WishlistItem.product_id == product_id,
            )
            .first()
        )
        return exists is not None


wishlist_service = WishlistService()
