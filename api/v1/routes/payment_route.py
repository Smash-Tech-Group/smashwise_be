"""
api/v1/routes/payment_route.py

Payment endpoints.

POST /payments/initialize/{order_id} — call Paystack, return auth URL
POST /payments/webhook               — Paystack webhook (NO auth header)
GET  /payments/{order_id}            — get payment status
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.payment import PaymentOut, PaystackWebhookPayload
from api.v1.services.payment_service import payment_service

payment = APIRouter(prefix="/payments", tags=["Payments"])


@payment.post(
    "/initialize/{order_id}",
    status_code=status.HTTP_200_OK,
    summary="Initialize Paystack payment for an order",
)
def initialize_payment(
    order_id: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Calls Paystack `/transaction/initialize`.
    Returns the `authorization_url` to redirect the user to for payment.
    Stores the transaction reference on the Payment record.
    """
    result = payment_service.initialize(db, user, order_id)
    return success_response(
        status_code=200,
        message="Payment initialized. Redirect user to authorization_url.",
        data=result,
    )


@payment.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Paystack webhook handler (no auth required)",
    include_in_schema=False,   # hide from public Swagger docs
)
async def paystack_webhook(
    request: Request,
    db:      Session = Depends(get_db),
):
    """
    Receives Paystack event notifications.

    Verifies the X-Paystack-Signature HMAC-SHA512 header.
    Always returns HTTP 200 — Paystack retries on non-200 responses.
    """
    payload_bytes = await request.body()
    signature     = request.headers.get("x-paystack-signature", "")

    try:
        payload_dict = await request.json()
        payload      = PaystackWebhookPayload(**payload_dict)
    except Exception:
        # Malformed payload — still return 200 to stop Paystack retrying
        return success_response(status_code=200, message="Webhook received.")

    payment_service.handle_webhook(db, payload_bytes, signature, payload)
    return success_response(status_code=200, message="Webhook processed.")


@payment.get(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    summary="Get payment status for an order",
)
def get_payment_status(
    order_id: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    pmt = payment_service.get_status(db, user, order_id)
    return success_response(
        status_code=200,
        message="Payment status retrieved.",
        data=jsonable_encoder(PaymentOut.model_validate(pmt)),
    )