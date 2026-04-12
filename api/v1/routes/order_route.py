"""
api/v1/routes/order_route.py

Order / checkout endpoints.

POST /orders/checkout          — convert cart → order
GET  /orders/                  — list orders (paginated)
GET  /orders/{order_id}        — get a single order
PATCH /orders/{order_id}/status — update order status
POST /orders/apply-promo       — validate a promo code
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.order import (
    CheckoutRequest,
    OrderOut,
    OrderStatusUpdate,
    PromoApplyRequest,
)
from api.v1.services.order_service import order_service

order = APIRouter(prefix="/orders", tags=["Orders"])


@order.post(
    "/checkout",
    status_code=status.HTTP_201_CREATED,
    summary="Checkout: convert active cart to an order",
)
def checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Creates an Order from the user's current cart.

    - Validates the cart is not empty.
    - Snapshots item prices at checkout time.
    - Calculates subtotal, delivery fee (home ₦2,800 / pickup ₦1,500),
      tax (7.5%), and total.
    - Applies promo discount if a valid code is provided.
    - Clears the cart after successful order creation.
    - Creates a pending Payment record ready for Paystack initialization.
    """
    new_order = order_service.checkout(db, user, request)
    return success_response(
        status_code=201,
        message="Order placed successfully.",
        data=jsonable_encoder(OrderOut.model_validate(new_order)),
    )


@order.post(
    "/apply-promo",
    status_code=status.HTTP_200_OK,
    summary="Validate a promo code and return the discount amount",
)
def apply_promo(
    request: PromoApplyRequest,
    user: User = Depends(get_current_user),
):
    result = order_service.apply_promo(request.code)
    return success_response(
        status_code=200,
        message="Promo code is valid.",
        data={
            "code":     result["code"],
            "discount": str(result["discount"]),
            "label":    result["label"],
        },
    )


@order.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List all orders for the authenticated user (paginated)",
)
def list_orders(
    skip:  int = Query(default=0,  ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db:    Session = Depends(get_db),
    user:  User    = Depends(get_current_user),
):
    total, orders = order_service.list_orders(db, user, skip, limit)
    try:
        total_pages = int(total / limit) + (total % limit > 0)
    except ZeroDivisionError:
        total_pages = 0

    return success_response(
        status_code=200,
        message="Orders retrieved successfully.",
        data={
            "total":       total,
            "total_pages": total_pages,
            "skip":        skip,
            "limit":       limit,
            "orders":      jsonable_encoder(
                [OrderOut.model_validate(o) for o in orders]
            ),
        },
    )


@order.get(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    summary="Get full details for a single order",
)
def get_order(
    order_id: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    o = order_service.get_order(db, user, order_id)
    return success_response(
        status_code=200,
        message="Order retrieved successfully.",
        data=jsonable_encoder(OrderOut.model_validate(o)),
    )


@order.patch(
    "/{order_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update order status (validates allowed transitions)",
)
def update_order_status(
    order_id: str,
    request:  OrderStatusUpdate,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    """
    Allowed transitions:
      pending    → processing | cancelled
      processing → completed  | cancelled
      completed  → (terminal — no transitions)
      cancelled  → (terminal — no transitions)
    """
    o = order_service.update_status(db, user, order_id, request)
    return success_response(
        status_code=200,
        message=f"Order status updated to '{o.status}'.",
        data=jsonable_encoder(OrderOut.model_validate(o)),
    )