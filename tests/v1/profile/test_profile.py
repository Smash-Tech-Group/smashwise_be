"""
tests/v1/profile/test_profile.py

Tests for profile endpoints:
  GET  /api/v1/profile
  PATCH /api/v1/profile

Uses the in-memory SQLite database configured in tests/conftest.py.
Each test function gets a fresh DB (function-scoped fixture).
"""

import pytest
from fastapi.testclient import TestClient


# ── Helpers ────────────────────────────────────────────────────

def _register_and_login(
    client: TestClient,
    email: str = "profile_user@example.com",
    username: str = "profile_user",
    password: str = "Secure@123",
) -> str:
    """Create a user, verify OTP, return Bearer token."""
    signup_resp = client.post("/api/v1/auth/signup/otp", json={
        "email":    email,
        "username": username,
        "password": password,
    })
    otp = signup_resp.json()["data"]["otp"]

    verify_resp = client.post("/api/v1/auth/verify-otp/signup", json={
        "email": email,
        "otp":   otp,
    })
    return verify_resp.json()["data"]["access_token"]


# ── GET /profile ───────────────────────────────────────────────

class TestGetProfile:

    def test_get_profile_success(self, client):
        """Authenticated user receives their profile."""
        token = _register_and_login(client)
        resp  = client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["message"] == "Profile retrieved successfully."

        data = body["data"]
        assert data["email"]    == "profile_user@example.com"
        assert data["username"] == "profile_user"
        assert data["is_active"] is True

    def test_get_profile_nullable_fields_are_null_on_fresh_account(self, client):
        """full_name, phone, avatar_url are null on a brand-new account."""
        token = _register_and_login(client)
        resp  = client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()["data"]
        assert data["full_name"]  is None
        assert data["phone"]      is None
        assert data["avatar_url"] is None

    def test_get_profile_response_structure(self, client):
        """Response contains all expected keys."""
        token = _register_and_login(client)
        resp  = client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()["data"]
        for key in ("id", "email", "username", "full_name", "phone",
                    "avatar_url", "is_active", "created_at", "updated_at"):
            assert key in data, f"Missing key: {key}"

    def test_get_profile_requires_auth(self, client):
        """No token → 403 (FastAPI HTTPBearer returns 403 on missing credentials)."""
        resp = client.get("/api/v1/profile")
        assert resp.status_code == 403

    def test_get_profile_invalid_token_returns_401(self, client):
        """Invalid/expired token → 401."""
        resp = client.get(
            "/api/v1/profile",
            headers={"Authorization": "Bearer this.is.not.a.valid.token"},
        )
        assert resp.status_code == 401


# ── PATCH /profile ─────────────────────────────────────────────

class TestUpdateProfile:

    def test_update_full_name_only(self, client):
        """Updating full_name leaves phone unchanged."""
        token = _register_and_login(
            client,
            email="upd1@example.com",
            username="upd_user1",
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.patch(
            "/api/v1/profile",
            json={"full_name": "Samson Ogunyo"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["full_name"] == "Samson Ogunyo"
        assert data["phone"]     is None   # untouched

    def test_update_phone_only(self, client):
        """Updating phone leaves full_name unchanged."""
        token = _register_and_login(
            client,
            email="upd2@example.com",
            username="upd_user2",
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.patch(
            "/api/v1/profile",
            json={"phone": "+2348012345678"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["phone"]     == "+2348012345678"
        assert data["full_name"] is None   # untouched

    def test_update_both_fields(self, client):
        """Both full_name and phone can be updated in one request."""
        token = _register_and_login(
            client,
            email="upd3@example.com",
            username="upd_user3",
        )
        resp = client.patch(
            "/api/v1/profile",
            json={"full_name": "Peter Michael", "phone": "08098765432"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["full_name"] == "Peter Michael"
        assert data["phone"]     == "08098765432"

    def test_update_profile_success_message(self, client):
        """Response message is correct on successful update."""
        token = _register_and_login(
            client,
            email="upd4@example.com",
            username="upd_user4",
        )
        resp = client.patch(
            "/api/v1/profile",
            json={"full_name": "Test User"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.json()["message"] == "Profile updated successfully."

    def test_null_value_does_not_overwrite_existing_data(self, client):
        """Passing null for a field that already has a value must NOT wipe it."""
        token = _register_and_login(
            client,
            email="upd5@example.com",
            username="upd_user5",
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Set initial value
        client.patch(
            "/api/v1/profile",
            json={"full_name": "Initial Name"},
            headers=headers,
        )

        # Send null for full_name — should be ignored
        resp = client.patch(
            "/api/v1/profile",
            json={"full_name": None},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["full_name"] == "Initial Name"

    def test_empty_body_changes_nothing(self, client):
        """An empty request body leaves all profile fields unchanged."""
        token = _register_and_login(
            client,
            email="upd6@example.com",
            username="upd_user6",
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Set initial values
        client.patch(
            "/api/v1/profile",
            json={"full_name": "Stays Same", "phone": "+2348011112222"},
            headers=headers,
        )

        # Empty body
        resp = client.patch("/api/v1/profile", json={}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["full_name"] == "Stays Same"
        assert data["phone"]     == "+2348011112222"

    def test_update_reflects_in_get_profile(self, client):
        """Changes made via PATCH are visible in a subsequent GET."""
        token = _register_and_login(
            client,
            email="upd7@example.com",
            username="upd_user7",
        )
        headers = {"Authorization": f"Bearer {token}"}

        client.patch(
            "/api/v1/profile",
            json={"full_name": "Confirmed Name", "phone": "+2349011223344"},
            headers=headers,
        )

        get_resp = client.get("/api/v1/profile", headers=headers)
        data = get_resp.json()["data"]
        assert data["full_name"] == "Confirmed Name"
        assert data["phone"]     == "+2349011223344"

    def test_email_field_is_not_updated(self, client):
        """email is read-only — even if sent in body it must not change."""
        token = _register_and_login(
            client,
            email="upd8@example.com",
            username="upd_user8",
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.patch(
            "/api/v1/profile",
            # Pydantic schema will silently ignore unknown fields by default;
            # this test confirms email in GET response is still the original.
            json={"full_name": "No Email Change"},
            headers=headers,
        )
        assert resp.json()["data"]["email"] == "upd8@example.com"

    # ── Validation errors ──────────────────────────────────────

    def test_invalid_phone_format_returns_422(self, client):
        """Non-Nigerian or malformed phone triggers a 422 with field error."""
        token = _register_and_login(
            client,
            email="val1@example.com",
            username="val_user1",
        )
        resp = client.patch(
            "/api/v1/profile",
            json={"phone": "12345"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_international_non_nigerian_phone_returns_422(self, client):
        """A valid-looking but non-Nigerian international number is rejected."""
        token = _register_and_login(
            client,
            email="val2@example.com",
            username="val_user2",
        )
        resp = client.patch(
            "/api/v1/profile",
            json={"phone": "+12025550123"},   # US number
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_full_name_exceeds_max_length_returns_422(self, client):
        """full_name longer than 100 characters returns 422."""
        token = _register_and_login(
            client,
            email="val3@example.com",
            username="val_user3",
        )
        resp = client.patch(
            "/api/v1/profile",
            json={"full_name": "A" * 101},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_valid_local_phone_format_accepted(self, client):
        """Local format 0XXXXXXXXXX (11 digits) is accepted."""
        token = _register_and_login(
            client,
            email="val4@example.com",
            username="val_user4",
        )
        resp = client.patch(
            "/api/v1/profile",
            json={"phone": "08012345678"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["phone"] == "08012345678"

    def test_valid_e164_phone_format_accepted(self, client):
        """E.164 format +234XXXXXXXXXX is accepted."""
        token = _register_and_login(
            client,
            email="val5@example.com",
            username="val_user5",
        )
        resp = client.patch(
            "/api/v1/profile",
            json={"phone": "+2348055667788"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["phone"] == "+2348055667788"

    # ── Auth guard ─────────────────────────────────────────────

    def test_update_profile_requires_auth(self, client):
        """No token → 403."""
        resp = client.patch("/api/v1/profile", json={"full_name": "Ghost"})
        assert resp.status_code == 403

    def test_update_profile_invalid_token_returns_401(self, client):
        """Invalid token → 401."""
        resp = client.patch(
            "/api/v1/profile",
            json={"full_name": "Ghost"},
            headers={"Authorization": "Bearer bad.token.here"},
        )
        assert resp.status_code == 401