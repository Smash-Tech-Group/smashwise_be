"""
api/v1/services/profile_service.py

Business logic for the Profile endpoints.

  get_profile()    — returns the authenticated user object as-is.
  update_profile() — applies a partial update; fields that are None
                     in the request body are SKIPPED so existing data
                     is never accidentally wiped.

Only full_name and phone are updatable via the profile endpoint.
email is read-only; avatar_url is reserved for a future upload feature.
"""

from sqlalchemy.orm import Session

from api.core.base.services import Service
from api.v1.models.user import User
from api.v1.schemas.profile import ProfileUpdate


class ProfileService(Service):
    # ── Abstract method stubs (required by Service base) ──────────
    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    # ── Public methods ─────────────────────────────────────────────

    def get_profile(self, db: Session, user: User) -> User:
        """
        Return the current authenticated user.

        Refreshes from DB to guarantee the latest data is returned
        (in case the session has a stale copy).
        """
        db.refresh(user)
        return user

    def update_profile(
        self, db: Session, user: User, data: ProfileUpdate
    ) -> User:
        """
        Apply a partial profile update.

        Only fields explicitly provided (non-None) in the request body
        are written to the database. Null / omitted fields are ignored
        so existing values are never overwritten unintentionally.
        """
        if data.full_name is not None:
            user.full_name = data.full_name

        if data.phone is not None:
            user.phone = data.phone

        db.commit()
        db.refresh(user)
        return user


profile_service = ProfileService()