from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.utils.jwt_handler import create_access_token
from api.utils.otp_store import generate_otp, verify_otp
from passlib.context import CryptContext

from api.core.base.services import Service
from api.v1.models.user import User
from api.v1.models.cart import Cart
from api.v1.schemas.auth import SignupRequest, LoginRequest
from api.utils.success_response import success_response

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService(Service):
    """Authentication service for handling registration and login"""

    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    # ------------------------------------------------------------------
    # Direct login — returns JWT immediately, no OTP step
    # ------------------------------------------------------------------

    def login(self, db: Session, data: LoginRequest):
        """
        Validate email + password and return a JWT access token directly.

        - 401 if user not found or password is wrong
        - 403 if account has not been activated yet (signup OTP not verified)
        """
        user = db.query(User).filter(User.email == data.email).first()

        # Use a generic message for both "not found" and "wrong password"
        # to avoid leaking which condition failed.
        if not user or not pwd_context.verify(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not activated. Please complete signup verification.",
            )

        token = create_access_token({"user_id": user.id})
        return success_response(
            status_code=200,
            message="Login successful.",
            data={"access_token": token, "token_type": "bearer", "user": user.to_dict()},
        )

    # ------------------------------------------------------------------
    # OTP: Signup flow
    # ------------------------------------------------------------------

    def signup_request_otp(self, db: Session, data: SignupRequest):
        """
        Register a new (inactive) account and return a 6-digit OTP.
        The account is activated only after verify_signup_otp() succeeds.
        """
        existing_user = db.query(User).filter(
            (User.email == data.email) | (User.username == data.username)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered.",
            )

        hashed = pwd_context.hash(data.password)
        new_user = User(
            email=data.email,
            username=data.username,
            hashed_password=hashed,
            is_active=False,  # activated once OTP is verified
        )
        db.add(new_user)
        db.flush()

        new_cart = Cart(user_id=new_user.id)
        db.add(new_cart)
        db.commit()
        db.refresh(new_user)

        otp_code = generate_otp("signup", data.email)
        return success_response(
            status_code=201,
            message="Account created. Please verify your OTP to activate your account.",
            data={"otp": otp_code},
        )

    def verify_signup_otp(self, db: Session, email: str, otp_code: str):
        """Verify the signup OTP and activate the account. Returns a JWT on success."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found for this email address.",
            )

        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is already verified.",
            )

        if not verify_otp("signup", email, otp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP. Please request a new one.",
            )

        user.is_active = True
        db.commit()
        db.refresh(user)

        token = create_access_token({"user_id": user.id})
        return success_response(
            status_code=200,
            message="Account verified successfully.",
            data={"access_token": token, "token_type": "bearer", "user": user.to_dict()},
        )


# Create singleton instance
auth_service = AuthService()