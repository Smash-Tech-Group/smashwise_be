"""
tests/v1/checkout/test_payments.py

Tests for payment endpoints.

Paystack API calls are mocked using unittest.mock so tests
run without a real Paystack account or network access.
"""

import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


# ── Helpers ────────────────────────────────────────────────────

def _register_and_login(client: TestClient, suffix: str = "") -> str:
    email    = f"pay_user{suffix}@example.com"
    username = f"pay_user{suffix}"
    signup = client.post("/api/v1/auth/signup/otp", json={
        "email": email, "username": username, "password": "Secure@123",
    })
    otp    = signup.json()["data"]["otp"]
    verify = client.post("/api/v1/auth/verify-otp/signup", json={"email": email, "otp": otp})
    return verify.json()["data"]["access_token"]


def _place_order(client: TestClient, token: str) -> str:
    client.post(
        "/api/v1/cart/items",
        json={
            "product_id":   "prod_pay",
            "product_name": "Test Product",
            "price":        5000,
            "quantity":     1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.post(
        "/api/v1/orders/checkout",
        json={"delivery_method": "pickup"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["data"]["id"]


def _make_paystack_signature(payload: dict, secret: str = "test_secret") -> str:
    payload_bytes = json.dumps(payload).encode()
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha512).hexdigest()


# ── Initialize payment tests ───────────────────────────────────

class TestInitializePayment:

    def test_initialize_payment_success(self, client):
        """Mock the Paystack HTTP call — verifies our service builds the right payload."""
        token    = _register_and_login(client, suffix="i1")
        order_id = _place_order(client, token)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": "https://checkout.paystack.com/abc123",
                "access_code":       "abc123",
                "reference":         "SMW-TESTREF001",
            },
        }
        mock_response.raise_for_status = MagicMock()

        with patch("api.v1.services.payment_service.http_requests.post",
                   return_value=mock_response):
            resp = client.post(
                f"/api/v1/payments/initialize/{order_id}",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "authorization_url" in data
        assert data["authorization_url"] == "https://checkout.paystack.com/abc123"
        assert data["reference"] == "SMW-TESTREF001"

    def test_initialize_nonexistent_order_returns_404(self, client):
        token = _register_and_login(client, suffix="i2")
        resp  = client.post(
            "/api/v1/payments/initialize/bad-order-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_initialize_other_users_order_returns_404(self, client):
        token_a  = _register_and_login(client, suffix="i3a")
        order_id = _place_order(client, token_a)

        token_b = _register_and_login(client, suffix="i3b")
        resp    = client.post(
            f"/api/v1/payments/initialize/{order_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    def test_initialize_already_paid_order_returns_400(self, client):
        token    = _register_and_login(client, suffix="i4")
        order_id = _place_order(client, token)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "authorization_url": "https://checkout.paystack.com/xyz",
                "access_code":       "xyz",
                "reference":         "SMW-PAID001",
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("api.v1.services.payment_service.http_requests.post",
                   return_value=mock_response):
            client.post(f"/api/v1/payments/initialize/{order_id}",
                        headers={"Authorization": f"Bearer {token}"})

        # Manually mark payment as paid via webhook
        ref = "SMW-PAID001"
        payload = {
            "event": "charge.success",
            "data":  {"reference": ref, "status": "success", "amount": 650000},
        }
        sig = _make_paystack_signature(payload, secret="")  # empty secret for test
        client.post(
            "/api/v1/payments/webhook",
            json=payload,
            headers={"x-paystack-signature": sig},
        )

        # Trying to initialize again should return 400
        with patch("api.v1.services.payment_service.http_requests.post",
                   return_value=mock_response):
            resp = client.post(
                f"/api/v1/payments/initialize/{order_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 400


# ── Get payment status tests ───────────────────────────────────

class TestGetPaymentStatus:
    def test_get_status_pending(self, client):
        token    = _register_and_login(client, suffix="g1")
        order_id = _place_order(client, token)

        resp = client.get(
            f"/api/v1/payments/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "pending"

    def test_get_status_other_user_returns_404(self, client):
        token_a  = _register_and_login(client, suffix="g2a")
        order_id = _place_order(client, token_a)

        token_b = _register_and_login(client, suffix="g2b")
        resp    = client.get(
            f"/api/v1/payments/{order_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404


# ── Webhook tests ─────────────────────────────────────────────

class TestPaystackWebhook:
    """
    Webhook tests use an empty PAYSTACK_SECRET_KEY (default in test env)
    so the HMAC computed in the service will be hmac("", payload, sha512).
    """

    def _webhook(self, client, payload: dict, secret: str = "") -> None:
        payload_bytes = json.dumps(payload).encode()
        sig           = hmac.new(secret.encode(), payload_bytes, hashlib.sha512).hexdigest()
        return client.post(
            "/api/v1/payments/webhook",
            content=payload_bytes,
            headers={
                "Content-Type":          "application/json",
                "x-paystack-signature":  sig,
            },
        )

    def test_webhook_charge_success_updates_payment(self, client):
        token    = _register_and_login(client, suffix="wh1")
        order_id = _place_order(client, token)

        # Initialize first so tx_reference is set
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "authorization_url": "https://checkout.paystack.com/test",
                "access_code":       "testcode",
                "reference":         "SMW-WEBHOOKTEST",
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("api.v1.services.payment_service.http_requests.post",
                   return_value=mock_response):
            client.post(f"/api/v1/payments/initialize/{order_id}",
                        headers={"Authorization": f"Bearer {token}"})

        payload = {
            "event": "charge.success",
            "data":  {"reference": "SMW-WEBHOOKTEST", "status": "success", "amount": 650000},
        }
        resp = self._webhook(client, payload)
        assert resp.status_code == 200

        # Payment status should now be "paid"
        status_resp = client.get(
            f"/api/v1/payments/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert status_resp.json()["data"]["status"] == "paid"

    def test_webhook_charge_failed_updates_payment(self, client):
        token    = _register_and_login(client, suffix="wh2")
        order_id = _place_order(client, token)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "authorization_url": "https://checkout.paystack.com/fail",
                "access_code":       "failcode",
                "reference":         "SMW-FAILTEST",
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("api.v1.services.payment_service.http_requests.post",
                   return_value=mock_response):
            client.post(f"/api/v1/payments/initialize/{order_id}",
                        headers={"Authorization": f"Bearer {token}"})

        payload = {
            "event": "charge.failed",
            "data":  {"reference": "SMW-FAILTEST", "status": "failed", "amount": 650000},
        }
        resp = self._webhook(client, payload)
        assert resp.status_code == 200

        status_resp = client.get(
            f"/api/v1/payments/{order_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert status_resp.json()["data"]["status"] == "failed"

    def test_webhook_invalid_signature_still_returns_200(self, client):
        """Paystack must always receive 200 — even on bad signatures."""
        payload = {
            "event": "charge.success",
            "data":  {"reference": "FAKE-REF", "status": "success", "amount": 100},
        }
        payload_bytes = json.dumps(payload).encode()
        resp = client.post(
            "/api/v1/payments/webhook",
            content=payload_bytes,
            headers={
                "Content-Type":         "application/json",
                "x-paystack-signature": "completelywrongsignature",
            },
        )
        assert resp.status_code == 200

    def test_webhook_unknown_reference_still_returns_200(self, client):
        """Unknown tx_reference should be silently ignored."""
        payload = {
            "event": "charge.success",
            "data":  {"reference": "UNKNOWN-REF", "status": "success", "amount": 100},
        }
        resp = self._webhook(client, payload)
        assert resp.status_code == 200