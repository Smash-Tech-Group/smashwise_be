"""
tests/v1/checkout/test_addresses.py

Tests for delivery address CRUD endpoints.

Uses the in-memory SQLite database configured in tests/conftest.py.
Each test function gets a fresh DB (function-scoped fixture).
"""

import pytest
from fastapi.testclient import TestClient


# ── Helpers ────────────────────────────────────────────────────

def _register_and_login(client: TestClient) -> str:
    """Create a user, verify OTP, return Bearer token."""
    signup_resp = client.post("/api/v1/auth/signup/otp", json={
        "email":    "addr_user@example.com",
        "username": "addr_user",
        "password": "Secure@123",
    })
    otp = signup_resp.json()["data"]["otp"]

    verify_resp = client.post("/api/v1/auth/verify-otp/signup", json={
        "email": "addr_user@example.com",
        "otp":   otp,
    })
    return verify_resp.json()["data"]["access_token"]


ADDRESS_PAYLOAD = {
    "category":       "home",
    "name":           "Home",
    "contact_person": "Peter Michael",
    "address":        "2 King Jaja Street, Hillside Estate, Gwarinpa, FCT Abuja",
    "is_default":     True,
}


# ── Tests ──────────────────────────────────────────────────────

class TestCreateAddress:
    def test_create_address_success(self, client):
        token = _register_and_login(client)
        resp = client.post(
            "/api/v1/addresses/",
            json=ADDRESS_PAYLOAD,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Home"
        assert data["is_default"] is True
        assert data["category"] == "home"

    def test_create_address_requires_auth(self, client):
        resp = client.post("/api/v1/addresses/", json=ADDRESS_PAYLOAD)
        assert resp.status_code == 403

    def test_create_address_invalid_category(self, client):
        token = _register_and_login(client)
        bad_payload = {**ADDRESS_PAYLOAD, "category": "spaceship"}
        resp = client.post(
            "/api/v1/addresses/",
            json=bad_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_first_address_becomes_default_automatically(self, client):
        """Even if is_default=False, the very first address is forced to default."""
        token = _register_and_login(client)
        resp = client.post(
            "/api/v1/addresses/",
            json={**ADDRESS_PAYLOAD, "is_default": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["is_default"] is True

    def test_second_default_clears_first(self, client):
        """Creating a second address with is_default=True should unset the first."""
        token = _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        first = client.post("/api/v1/addresses/", json=ADDRESS_PAYLOAD, headers=headers)
        first_id = first.json()["data"]["id"]

        client.post(
            "/api/v1/addresses/",
            json={
                **ADDRESS_PAYLOAD,
                "name": "Work",
                "category": "work",
                "is_default": True,
            },
            headers=headers,
        )

        # Fetch first address — should no longer be default
        resp = client.get(f"/api/v1/addresses/{first_id}", headers=headers)
        assert resp.json()["data"]["is_default"] is False


class TestListAddresses:
    def test_list_empty(self, client):
        token = _register_and_login(client)
        resp = client.get(
            "/api/v1/addresses/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["addresses"] == []

    def test_list_returns_only_own_addresses(self, client):
        """Two users should not see each other's addresses."""
        token_a = _register_and_login(client)
        # Register second user
        signup_resp = client.post("/api/v1/auth/signup/otp", json={
            "email": "other@example.com", "username": "other_user", "password": "Other@123",
        })
        otp = signup_resp.json()["data"]["otp"]
        verify = client.post("/api/v1/auth/verify-otp/signup", json={
            "email": "other@example.com",
            "otp": otp,
        })
        token_b = verify.json()["data"]["access_token"]

        client.post("/api/v1/addresses/", json=ADDRESS_PAYLOAD,
                    headers={"Authorization": f"Bearer {token_a}"})

        resp = client.get("/api/v1/addresses/",
                          headers={"Authorization": f"Bearer {token_b}"})
        assert resp.json()["data"]["addresses"] == []


class TestUpdateAddress:
    def test_update_address_success(self, client):
        token = _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        create_resp = client.post("/api/v1/addresses/", json=ADDRESS_PAYLOAD, headers=headers)
        addr_id = create_resp.json()["data"]["id"]

        resp = client.patch(
            f"/api/v1/addresses/{addr_id}",
            json={"name": "My Home", "contact_person": "Updated Name"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "My Home"
        assert resp.json()["data"]["contact_person"] == "Updated Name"

    def test_update_another_users_address_returns_403(self, client):
        token_a = _register_and_login(client)

        create_resp = client.post(
            "/api/v1/addresses/", json=ADDRESS_PAYLOAD,
            headers={"Authorization": f"Bearer {token_a}"},
        )
        addr_id = create_resp.json()["data"]["id"]

        # Register a second user
        signup = client.post("/api/v1/auth/signup/otp", json={
            "email": "hacker@example.com", "username": "hacker", "password": "Hacker@123",
        })
        otp = signup.json()["data"]["otp"]
        verify = client.post("/api/v1/auth/verify-otp/signup", json={
            "email": "hacker@example.com", "otp": otp,
        })
        token_b = verify.json()["data"]["access_token"]

        resp = client.patch(
            f"/api/v1/addresses/{addr_id}",
            json={"name": "Stolen"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 403


class TestDeleteAddress:
    def test_delete_address_success(self, client):
        token = _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        create_resp = client.post("/api/v1/addresses/", json=ADDRESS_PAYLOAD, headers=headers)
        addr_id = create_resp.json()["data"]["id"]

        resp = client.delete(f"/api/v1/addresses/{addr_id}", headers=headers)
        assert resp.status_code == 200

        # Confirm it's gone
        get_resp = client.get(f"/api/v1/addresses/{addr_id}", headers=headers)
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        token = _register_and_login(client)
        resp = client.delete(
            "/api/v1/addresses/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestSetDefault:
    def test_set_default_switches_correctly(self, client):
        token = _register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        a1 = client.post("/api/v1/addresses/", json=ADDRESS_PAYLOAD, headers=headers).json()["data"]["id"]
        a2 = client.post(
            "/api/v1/addresses/",
            json={**ADDRESS_PAYLOAD, "name": "Work", "category": "work", "is_default": False},
            headers=headers,
        ).json()["data"]["id"]

        resp = client.patch(f"/api/v1/addresses/{a2}/set-default", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["is_default"] is True

        # Old default should now be False
        a1_resp = client.get(f"/api/v1/addresses/{a1}", headers=headers)
        assert a1_resp.json()["data"]["is_default"] is False