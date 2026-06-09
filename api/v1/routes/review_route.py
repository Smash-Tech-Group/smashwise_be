"""
api/v1/routes/review_route.py

Review purchase endpoints.

All routes require authentication.

Routes:
  POST /reviews                          — submit a new review
  GET  /orders/{order_id}/reviewable     — list reviewable line items
  GET  /products/{product_id}/can-review — check if user can review product
"""

# File: api/v1/routes/review_route.py

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.product import ReviewSubmit, ReviewOut, CanReviewOut
from api.v1.services.review_service import review_service

review = APIRouter(tags=["Reviews"])


@review.post(
    "/reviews",
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review for a purchased order line item",
)
def submit_review(
    payload: ReviewSubmit,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    """
    Submit a product review tied to a specific order line item.

    - Returns **201** on success with the created review.
    - Returns **409** if a review already exists for that line item.
    - Returns **404** if the line item doesn't belong to the user.
    - Returns **401** if unauthenticated.
    """
    new_review = review_service.submit_review(db, user, payload)
    return success_response(
        status_code=201,
        message="Review submitted successfully.",
        data=jsonable_encoder(ReviewOut.model_validate(new_review)),
    )


@review.get(
    "/orders/{order_id}/reviewable",
    status_code=status.HTTP_200_OK,
    summary="List order line items eligible for review",
)
def get_reviewable_items(
    order_id: str,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    """
    Return only line items from this order that are:
      - In a delivered order
      - Not yet reviewed by this user

    Returns an empty list if the order is not yet delivered.
    Returns **404** if the order doesn't belong to the user.
    """
    items = review_service.get_reviewable_items(db, user, order_id)
    return success_response(
        status_code=200,
        message="Reviewable items retrieved successfully.",
        data={
            "order_id": order_id,
            "items": jsonable_encoder([
                {
                    "id":            item.id,
                    "product_id":    item.product_id,
                    "product_name":  item.product_name,
                    "product_image": item.product_image,
                    "unit_price":    item.unit_price,
                    "quantity":      item.quantity,
                }
                for item in items
            ]),
        },
    )


@review.get(
    "/products/{product_id}/can-review",
    status_code=status.HTTP_200_OK,
    summary="Check if the current user can review a product",
)
def can_review_product(
    product_id: str,
    db:         Session = Depends(get_db),
    user:       User    = Depends(get_current_user),
):
    """
    Returns **{ "can_review": true }** only if the user has a delivered
    order containing this product with no existing review.
    """
    eligible = review_service.can_review_product(db, user, product_id)
    return success_response(
        status_code=200,
        message="Review eligibility checked.",
        data=jsonable_encoder(CanReviewOut(can_review=eligible)),
    )