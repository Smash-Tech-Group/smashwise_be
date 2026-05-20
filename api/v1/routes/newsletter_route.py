"""
api/v1/routes/newsletter_route.py

Newsletter subscription endpoint.

POST /api/v1/newsletter/subscribe
  — Public route (no JWT required).
  — Accepts { email } in the request body.
  — Returns 201 on first subscription, 409 if already subscribed,
    422 if email format is invalid.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.schemas.subscription import SubscriptionCreate, SubscriptionOut
from api.v1.services.subscription_service import subscription_service

newsletter = APIRouter(prefix="/newsletter", tags=["Newsletter"])


@newsletter.post(
    "/subscribe",
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe an email address to the newsletter",
    response_description="Subscription created successfully",
)
def subscribe(
    request: SubscriptionCreate,
    db: Session = Depends(get_db),
):
    """
    Subscribe to the Smashwise newsletter.

    - Email must be a valid RFC-5322 address — returns 422 otherwise.
    - Duplicate emails return 409 with a descriptive message.
    - No authentication required — open to all visitors.
    """
    sub = subscription_service.subscribe(db, request.email)
    return success_response(
        status_code=201,
        message="Subscribed successfully. Welcome to Smashwise!",
        data=SubscriptionOut.model_validate(sub).model_dump(),
    )