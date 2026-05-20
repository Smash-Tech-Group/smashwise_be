"""
tests/v1/newsletter/test_subscribe.py

Tests for the newsletter subscription endpoint:
  POST /api/v1/newsletter/subscribe

Uses the in-memory SQLite database configured in tests/conftest.py.
Each test function gets a fresh DB (function-scoped fixture).
No authentication required — this is a public endpoint.
"""

import pytest


# ── POST /newsletter/subscribe ─────────────────────────────────

class TestNewsletterSubscribe:

    def test_subscribe_success(self, client):
        """Valid email creates a subscription and returns 201."""
        resp = client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": "newuser@example.com"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["message"] == "Subscribed successfully. Welcome to Smashwise!"

    def test_subscribe_response_contains_email(self, client):
        """Response data includes the normalised email and an id."""
        resp = client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": "datacheck@example.com"},
        )
        data = resp.json()["data"]
        assert data["email"] == "datacheck@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_subscribe_normalises_email_to_lowercase(self, client):
        """Emails are stored in lowercase regardless of input casing."""
        resp = client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": "MixedCase@Example.COM"},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["email"] == "mixedcase@example.com"

    def test_subscribe_duplicate_returns_409(self, client):
        """Subscribing the same email twice returns 409 Conflict."""
        payload = {"email": "duplicate@example.com"}
        client.post("/api/v1/newsletter/subscribe", json=payload)

        resp = client.post("/api/v1/newsletter/subscribe", json=payload)
        assert resp.status_code == 409
        assert "already subscribed" in resp.json()["message"].lower()

    def test_subscribe_duplicate_case_insensitive_returns_409(self, client):
        """Duplicate check is case-insensitive — UPPER and lower are the same email."""
        client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": "case@example.com"},
        )
        resp = client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": "CASE@EXAMPLE.COM"},
        )
        assert resp.status_code == 409

    def test_subscribe_invalid_email_returns_422(self, client):
        """Malformed email address triggers a 422 Unprocessable Entity."""
        resp = client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": "not-an-email"},
        )
        assert resp.status_code == 422

    def test_subscribe_missing_email_field_returns_422(self, client):
        """Missing email field in request body returns 422."""
        resp = client.post(
            "/api/v1/newsletter/subscribe",
            json={},
        )
        assert resp.status_code == 422

    def test_subscribe_empty_string_email_returns_422(self, client):
        """Empty string email is not a valid address — returns 422."""
        resp = client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": ""},
        )
        assert resp.status_code == 422

    def test_subscribe_no_auth_required(self, client):
        """No Authorization header is needed — public endpoint."""
        resp = client.post(
            "/api/v1/newsletter/subscribe",
            json={"email": "noauth@example.com"},
            # No Authorization header
        )
        assert resp.status_code == 201

    def test_multiple_unique_emails_all_succeed(self, client):
        """Each unique email address creates its own subscription record."""
        emails = [
            "alpha@example.com",
            "beta@example.com",
            "gamma@example.com",
        ]
        for email in emails:
            resp = client.post(
                "/api/v1/newsletter/subscribe",
                json={"email": email},
            )
            assert resp.status_code == 201, f"Failed for {email}"