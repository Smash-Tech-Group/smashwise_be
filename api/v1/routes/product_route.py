"""
api/v1/routes/product_route.py

Product catalog endpoints.

Public routes (no auth required):
  GET  /products/                        — paginated product list
  GET  /products/{product_id}            — single product detail
  GET  /products/{product_id}/reviews    — product reviews
  GET  /products/{product_id}/rating-breakdown — rating counts
  GET  /products/{product_id}/recommended     — recommended products

Authenticated routes:
  POST /products/{product_id}/reviews    — create a review
  POST /products/seed                    — seed mock products (dev/admin)
"""

from fastapi import APIRouter, Depends, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.product import (
    ProductOut,
    ProductListOut,
    ReviewCreate,
    ReviewOut,
    RatingBreakdownOut,
)
from api.v1.services.product_service import product_service

product = APIRouter(prefix="/products", tags=["Products"])


@product.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List all products (paginated, filterable)",
)
def list_products(
    skip:     int = Query(default=0, ge=0),
    limit:    int = Query(default=20, ge=1, le=100),
    category: str = Query(default=None),
    search:   str = Query(default=None),
    db:       Session = Depends(get_db),
):
    total, products = product_service.get_products(db, skip, limit, category, search)
    items = []
    for p in products:
        first_image = None
        if p.images:
            sorted_imgs = sorted(p.images, key=lambda img: img.sort_order)
            first_image = sorted_imgs[0].url if sorted_imgs else None
        item_dict = {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "old_price": p.old_price,
            "badge": p.badge,
            "stock_status": p.stock_status,
            "rating": p.rating,
            "review_count": p.review_count,
            "category": p.category,
            "vendor": p.vendor,
            "image": first_image,
        }
        items.append(item_dict)

    return success_response(
        status_code=200,
        message="Products retrieved successfully.",
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "products": jsonable_encoder(items),
        },
    )


@product.get(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single product with full details",
)
def get_product(product_id: str, db: Session = Depends(get_db)):
    p = product_service.get_product(db, product_id)
    return success_response(
        status_code=200,
        message="Product retrieved successfully.",
        data=jsonable_encoder(ProductOut.model_validate(p)),
    )


@product.get(
    "/{product_id}/reviews",
    status_code=status.HTTP_200_OK,
    summary="List all reviews for a product",
)
def get_reviews(product_id: str, db: Session = Depends(get_db)):
    reviews = product_service.get_reviews(db, product_id)
    return success_response(
        status_code=200,
        message="Reviews retrieved successfully.",
        data={
            "reviews": jsonable_encoder(
                [ReviewOut.model_validate(r) for r in reviews]
            )
        },
    )


@product.post(
    "/{product_id}/reviews",
    status_code=status.HTTP_201_CREATED,
    summary="Create a product review",
)
def create_review(
    product_id: str,
    request: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    review = product_service.create_review(db, user, product_id, request)
    return success_response(
        status_code=201,
        message="Review created successfully.",
        data=jsonable_encoder(ReviewOut.model_validate(review)),
    )


@product.get(
    "/{product_id}/rating-breakdown",
    status_code=status.HTTP_200_OK,
    summary="Get rating breakdown for a product",
)
def get_rating_breakdown(product_id: str, db: Session = Depends(get_db)):
    breakdown = product_service.get_rating_breakdown(db, product_id)
    return success_response(
        status_code=200,
        message="Rating breakdown retrieved.",
        data=breakdown,
    )


@product.get(
    "/{product_id}/recommended",
    status_code=status.HTTP_200_OK,
    summary="Get recommended products",
)
def get_recommended(
    product_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    products = product_service.get_recommended(db, product_id, limit)
    items = []
    for p in products:
        first_image = None
        if p.images:
            sorted_imgs = sorted(p.images, key=lambda img: img.sort_order)
            first_image = sorted_imgs[0].url if sorted_imgs else None
        items.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "old_price": p.old_price,
            "badge": p.badge,
            "stock_status": p.stock_status,
            "rating": p.rating,
            "review_count": p.review_count,
            "category": p.category,
            "vendor": p.vendor,
            "image": first_image,
        })
    return success_response(
        status_code=200,
        message="Recommended products retrieved.",
        data={"products": jsonable_encoder(items)},
    )


@product.post(
    "/seed",
    status_code=status.HTTP_201_CREATED,
    summary="Seed mock products into the database (dev/admin)",
)
def seed_products(db: Session = Depends(get_db)):
    products = product_service.seed_products(db)
    return success_response(
        status_code=201,
        message=f"{len(products)} products seeded successfully.",
        data={"count": len(products)},
    )
