"""
api/v1/services/payment_service.py

Payment business logic.

  initialize()      — calls Paystack /transaction/initialize, stores
                       authorization_url and tx_reference on the Payment row.
  handle_webhook()  — verifies HMAC-SHA512 signature, updates Payment and
                       Order statuses.
  get_status()      — returns the Payment row for a given order.

PAYSTACK_SECRET_KEY must be set in .env.
To switch payment providers in the future, only this file needs to change.
"""

import hmac
import hashlib
import uuid
import requests as http_requests

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.core.base.services import Service
from api.v1.models.order import Order
from api.v1.models.payment import Payment
from api.v1.models.user import User
from api.v1.schemas.payment import PaystackWebhookPayload
from api.utils.settings import settings

PAYSTACK_BASE_URL = "https://api.paystack.co"


class PaymentService(Service):
    # ── Abstract method stubs ──────────────────────────────────
    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    # ── Helpers ────────────────────────────────────────────────

    def _get_order_payment(
        self, db: Session, user: User, order_id: str
    ) -> tuple[Order, Payment]:
        order = (
            db.query(Order)
            .filter(Order.id == order_id, Order.user_id == user.id)
            .first()
        )
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )
        payment = (
            db.query(Payment)
            .filter(Payment.order_id == order_id)
            .first()
        )
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment record not found for this order.",
            )
        return order, payment

    # ── Initialize payment ────────────────────────────────────

    def initialize(self, db: Session, user: User, order_id: str) -> dict:
        """
        Call Paystack /transaction/initialize and store the returned
        authorization URL and reference on the Payment row.

        Returns a dict with:
          authorization_url, access_code, reference, payment (PaymentOut dict)
        """
        order, payment = self._get_order_payment(db, user, order_id)

        if payment.status == "paid":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This order has already been paid.",
            )

        # Amount in kobo (Paystack expects integer kobo)
        amount_kobo = int(order.total * 100)

        # Generate a unique reference
        reference = f"SMW-{uuid.uuid4().hex[:12].upper()}"

        payload = {
            "email":     user.email,
            "amount":    amount_kobo,
            "reference": reference,
            "metadata": {
                "order_id":   order.id,
                "user_id":    user.id,
                "cancel_url": f"{settings.FRONTEND_URL}/checkout",
            },
        }

        try:
            resp = http_requests.post(
                f"{PAYSTACK_BASE_URL}/transaction/initialize",
                json=payload,
                headers={
                    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                    "Content-Type":  "application/json",
                },
                timeout=15,
            )
            resp.raise_for_status()
            ps_data = resp.json()["data"]
        except http_requests.RequestException as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Paystack API error: {exc}",
            )

        # Persist the Paystack response
        payment.tx_reference      = ps_data["reference"]
        payment.authorization_url = ps_data["authorization_url"]
        payment.payment_metadata  = ps_data
        db.commit()
        db.refresh(payment)

        return {
            "authorization_url": ps_data["authorization_url"],
            "access_code":       ps_data["access_code"],
            "reference":         ps_data["reference"],
            "payment":           payment.to_dict(),
        }

    # ── Webhook ───────────────────────────────────────────────

    @staticmethod
    def _verify_signature(payload_bytes: bytes, signature: str) -> bool:
        secret = settings.PAYSTACK_SECRET_KEY.encode()
        computed = hmac.new(secret, payload_bytes, hashlib.sha512).hexdigest()
        return hmac.compare_digest(computed, signature)

    def handle_webhook(
        self,
        db: Session,
        payload_bytes: bytes,
        signature: str,
        payload: PaystackWebhookPayload,
    ) -> None:
        """
        Verify Paystack HMAC-SHA512 signature, then update Payment and
        Order statuses accordingly.

        Always returns without raising so the caller can respond 200
        to Paystack regardless (Paystack retries on non-200 responses).
        """
        if not self._verify_signature(payload_bytes, signature):
            # Log the failure but do NOT raise — Paystack must receive 200
            from api.loggers.app_logger import app_logger
            app_logger.warning("Paystack webhook received with invalid signature.")
            return

        reference = payload.data.reference
        payment = (
            db.query(Payment)
            .filter(Payment.tx_reference == reference)
            .first()
        )
        if not payment:
            return  # Unknown reference — ignore silently

        if payload.event == "charge.success":
            payment.status = "paid"
            # Advance the order to processing
            order = payment.order
            if order and order.status == "pending":
                order.status = "processing"
        else:
            payment.status = "failed"

        db.commit()

    # ── Get status ────────────────────────────────────────────

    def get_status(self, db: Session, user: User, order_id: str) -> Payment:
        _, payment = self._get_order_payment(db, user, order_id)
        return payment


payment_service = PaymentService()