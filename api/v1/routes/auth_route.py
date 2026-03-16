from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.auth import (
    SignInRequest,
    SignupRequest,
    LoginRequest,
    OTPVerifyRequest,
    UserOut,
)
from api.v1.services.auth import auth_service

auth = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Login — direct JWT, no OTP step
# ---------------------------------------------------------------------------

@auth.post("/login", status_code=status.HTTP_200_OK, summary="Login and receive a JWT")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password and receive a JWT access token.

    - **email**: must be a valid email address
    - **password**: minimum 8 characters; at least one uppercase letter, one number, and one special character
    - Returns **401** for invalid credentials
    - Returns **403** if the account has not been activated via signup OTP yet
    """
    return auth_service.login(db, request)


# ---------------------------------------------------------------------------
# OTP: Signup flow  POST /signup/otp → POST /verify-otp/signup
# ---------------------------------------------------------------------------

@auth.post(
    "/signup/otp",
    status_code=status.HTTP_201_CREATED,
    summary="Register and receive a signup OTP",
)
def signup_request_otp(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Create a new (inactive) account and receive a 6-digit OTP.
    The account is only activated after `POST /verify-otp/signup` is called
    with the correct OTP within 5 minutes.
    """
    return auth_service.signup_request_otp(db, request)


@auth.post(
    "/verify-otp/signup",
    status_code=status.HTTP_200_OK,
    summary="Verify signup OTP and activate account",
)
def verify_signup_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify the 6-digit OTP issued during signup.
    On success the account is activated and a JWT access token is returned.
    The OTP is invalidated immediately after use or after 5 minutes.
    """
    return auth_service.verify_signup_otp(db, request.email, request.otp)


# ---------------------------------------------------------------------------
# /me — requires authentication
# ---------------------------------------------------------------------------

@auth.get("/me", status_code=status.HTTP_200_OK, summary="Get the authenticated user")
def get_me(current_user: User = Depends(get_current_user)):
    user_out = UserOut.model_validate(current_user)
    return success_response(
        status_code=200,
        message="User retrieved",
        data=user_out.model_dump(),
    )


# ---------------------------------------------------------------------------
# Legacy /signin stub (kept for backward-compat)
# ---------------------------------------------------------------------------

@auth.post(
    "/signin",
    status_code=status.HTTP_200_OK,
    summary="Sign In via phone (stub)",
)
def signin_request_otp(
    request: SignInRequest,
    db: Session = Depends(get_db),
):
    return success_response(
        status_code=status.HTTP_200_OK,
        message="Sign in request OTP endpoint (stub)",
        data={},
    )
