"""
api/v1/routes/profile_route.py

Profile endpoints.

GET  /profile  — retrieve the authenticated user's profile
PATCH /profile — partially update the authenticated user's profile

Both routes require a valid JWT Bearer token.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.profile import ProfileOut, ProfileUpdate
from api.v1.services.profile_service import profile_service

profile = APIRouter(prefix="/profile", tags=["Profile"])


@profile.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get the authenticated user's profile",
    response_description="Returns the current user's profile data",
)
def get_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve profile for the currently authenticated user.

    - Nullable fields (`full_name`, `phone`, `avatar_url`) return `null`
      when not yet set — this is expected and not an error.
    - Requires `Authorization: Bearer <token>` header.
    """
    profile_data = profile_service.get_profile(db, user)
    return success_response(
        status_code=200,
        message="Profile retrieved successfully.",
        data=ProfileOut.model_validate(profile_data).model_dump(),
    )


@profile.patch(
    "",
    status_code=status.HTTP_200_OK,
    summary="Partially update the authenticated user's profile",
    response_description="Returns the updated profile data",
)
def update_profile(
    request: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Partially update profile for the currently authenticated user.

    - Only fields included in the request body are updated.
    - Omitting a field (or passing `null`) leaves the existing value unchanged.
    - `email` is read-only and cannot be changed via this endpoint.
    - Requires `Authorization: Bearer <token>` header.

    **Updatable fields:**
    - `full_name` — display name, max 100 characters
    - `phone` — Nigerian phone number (`+234XXXXXXXXXX` or `0XXXXXXXXXX`)
    """
    updated_user = profile_service.update_profile(db, user, request)
    return success_response(
        status_code=200,
        message="Profile updated successfully.",
        data=ProfileOut.model_validate(updated_user).model_dump(),
    )