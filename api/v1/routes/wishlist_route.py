"""
api/v1/routes/wishlist_route.py

Wishlist endpoints. All routes require JWT authentication.

GET    /wishlist/               — list wishlist items
POST   /wishlist/               — add product to wishlist
DELETE /wishlist/{product_id}   — remove from wishlist
GET    /wishlist/check/{product_id} — check if product is in wishlist
"""

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.wishlist import WishlistItemAdd
from api.v1.services.wishlist_service import wishlist_service

wishlist = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@wishlist.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List all wishlist items for the authenticated user",
)
def list_wishlist(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    items = wishlist_service.get_wishlist(db, user)
    return success_response(
        status_code=200,
        message="Wishlist retrieved successfully.",
        data={"items": jsonable_encoder(items)},
    )


@wishlist.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Add a product to the wishlist",
)
def add_to_wishlist(
    request: WishlistItemAdd,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    item = wishlist_service.add_to_wishlist(db, user, request.product_id)
    return success_response(
        status_code=201,
        message="Product added to wishlist.",
        data=jsonable_encoder(item),
    )


@wishlist.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove a product from the wishlist",
)
def remove_from_wishlist(
    product_id: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    wishlist_service.remove_from_wishlist(db, user, product_id)
    return success_response(
        status_code=200,
        message="Product removed from wishlist.",
    )


@wishlist.get(
    "/check/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Check if a product is in the wishlist",
)
def check_wishlist(
    product_id: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    in_wishlist = wishlist_service.check_wishlist(db, user, product_id)
    return success_response(
        status_code=200,
        message="Wishlist status checked.",
        data={"in_wishlist": in_wishlist},
    )
