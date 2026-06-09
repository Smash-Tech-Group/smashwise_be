"""
api/v1/services/review_service.py

Business logic for the review purchase feature.

Handles:
  - Submitting a new review tied to an order line item
  - Fetching reviewable (delivered + unreviewed) line items for an order
  - Checking whether the current user can review a specific product
"""

# File: api/v1/services/review_service.py

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.v1.models.product import ProductReview
from api.v1.models.order import Order, OrderItem
from api.v1.models.user import User
from api.v1.schemas.product import ReviewSubmit


class ReviewService:

    # ── Submit a review ────────────────────────────────────────

    def submit_review(
        self,
        db:      Session,
        user:    User,
        payload: ReviewSubmit,
    ) -> ProductReview:
        """
        Create a new ProductReview tied to an order line item.

        Raises:
          409  — a review already exists for this order_line_item_id
          404  — the order line item doesn't exist or doesn't belong to user
        """
        # Verify the line item belongs to the authenticated user
        item = (
            db.query(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                OrderItem.id == payload.order_line_item_id,
                Order.user_id == user.id,
            )
            .first()
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order line item not found or does not belong to this user.",
            )

        # Guard: one review per line item
        existing = (
            db.query(ProductReview)
            .filter(ProductReview.order_line_item_id == payload.order_line_item_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A review already exists for this order line item.",
            )

        review = ProductReview(
            product_id         = payload.product_id,
            user_id            = user.id,
            order_line_item_id = payload.order_line_item_id,
            reviewer_name      = payload.reviewer_name,
            title              = payload.title,
            rating             = payload.rating,
            comment            = payload.body,
            media_urls         = payload.media_urls or [],
            verified           = True,   # purchase-confirmed
        )
        db.add(review)

        # Update aggregate rating on the product
        self._update_product_rating(db, payload.product_id)

        db.commit()
        db.refresh(review)
        return review

    # ── Reviewable line items ──────────────────────────────────

    def get_reviewable_items(
        self,
        db:       Session,
        user:     User,
        order_id: str,
    ) -> list[OrderItem]:
        """
        Return OrderItems eligible for review:
          - Parent order belongs to user
          - Order status == 'delivered'
          - No existing ProductReview for this line item
        """
        order = (
            db.query(Order)
            .filter(Order.id == order_id, Order.user_id == user.id)
            .first()
        )
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        if order.status != "delivered":
            return []

        # Items with no associated review
        reviewed_item_ids = (
            db.query(ProductReview.order_line_item_id)
            .filter(ProductReview.order_line_item_id.isnot(None))
            .subquery()
        )

        items = (
            db.query(OrderItem)
            .filter(
                OrderItem.order_id == order_id,
                ~OrderItem.id.in_(reviewed_item_ids),
            )
            .all()
        )
        return items

    # ── Can review check ───────────────────────────────────────

    def can_review_product(
        self,
        db:         Session,
        user:       User,
        product_id: str,
    ) -> bool:
        """
        Return True only if:
          - User has a delivered order containing this product_id
          - That line item has no existing review
        """
        # Find delivered order items for this user + product
        delivered_items = (
            db.query(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.user_id   == user.id,
                Order.status    == "delivered",
                OrderItem.product_id == product_id,
            )
            .all()
        )

        if not delivered_items:
            return False

        # Check if any of those items is still unreviewed
        for item in delivered_items:
            reviewed = (
                db.query(ProductReview)
                .filter(ProductReview.order_line_item_id == item.id)
                .first()
            )
            if not reviewed:
                return True

        return False

    # ── Private helpers ────────────────────────────────────────

    def _update_product_rating(self, db: Session, product_id: str) -> None:
        """Recalculate and persist the aggregate rating for a product."""
        from api.v1.models.product import Product
        from sqlalchemy import func

        result = (
            db.query(
                func.avg(ProductReview.rating).label("avg_rating"),
                func.count(ProductReview.id).label("review_count"),
            )
            .filter(ProductReview.product_id == product_id)
            .one()
        )

        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.rating       = round(float(result.avg_rating or 0), 1)
            product.review_count = result.review_count
            db.add(product)


review_service = ReviewService()