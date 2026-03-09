from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.schemas.auth import (

    SignInRequest,

)

auth = APIRouter(prefix="/auth", tags=["Authentication"])





@auth.post(
    "/signin",
    status_code=status.HTTP_200_OK,
    summary="Sign In: Request OTP",
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


