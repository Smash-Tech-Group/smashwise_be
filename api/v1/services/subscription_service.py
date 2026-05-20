"""
api/v1/services/subscription_service.py

Business logic for the newsletter subscription feature.

subscribe(db, email)
  - Normalises the email to lowercase.
  - Returns the existing record if already subscribed (idempotent check)
    but raises 409 so the caller can surface a friendly "already subscribed"
    message to the user.
  - Creates and persists a new Subscription record on first sign-up.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.core.base.services import Service
from api.v1.models.subscription import Subscription


class SubscriptionService(Service):
    # ── Abstract method stubs (required by Service base) ──────────
    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    # ── Public methods ─────────────────────────────────────────────

    def subscribe(self, db: Session, email: str) -> Subscription:
        """
        Subscribe an email address to the newsletter.

        Raises:
            HTTPException 409 — if the email is already subscribed.
        Returns:
            The newly created Subscription record.
        """
        normalised = email.strip().lower()

        existing = (
            db.query(Subscription)
            .filter(Subscription.email == normalised)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email is already subscribed.",
            )

        subscription = Subscription(email=normalised)
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription


subscription_service = SubscriptionService()