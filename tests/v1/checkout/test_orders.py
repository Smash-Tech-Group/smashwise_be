"""
tests/v1/checkout/test_orders.py

Tests for checkout and order lifecycle endpoints.
"""

import pytest
from fastapi.testclient import TestClient


# ── Helpers ────────────────────────────────────────────────────

def _register_and_login(client: TestClient, suffix: str = "") -> str:
    email    = f"order_user{suffix}@example.com"
    username = f"order_user{suffix}"
    signup = client.post("/api/v1/auth/signup/otp", json={
        "email": email, "username": username, "password": "Secure@123",
    })
    otp = signup.json()["data"]["otp"]
    verify = client.post("/api/v1/auth/verify-otp/signup", json={"email": email, "otp": otp})
    return verify.json()["data"]["access_token"]


def _add_cart_item(client: TestClient, token: str, product_id: str = "prod_001") -> None:
    client.post(
        "/api/v1/cart/items",
        json={
            "product_id":    product_id,
            "product_name":  "Men Lace-up Shoes",
            "product_image": "https://example.com/shoe.png",
            "price":         11900,
            "quantity":      2,
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def _create_address(client: TestClient, token: str) -> str:
    resp = client.post(
        "/api/v1/addresses/",
        json={
            "category":       "home",
            "name":           "Home",
            "contact_person": "Test User",
            "address":        "1 Test Street, Lagos",
            "is_default":     True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["data"]["id"]


# ── Checkout tests ─────────────────────────────────────────────

class TestCheckout:
    def test_checkout_home_delivery_success(self, client):
        token    = _register_and_login(client)
        addr_id  = _create_address(client, token)
        _add_cart_item(client, token)

        resp = client.post(
            "/api/v1/orders/checkout",
            json={"address_id": addr_id, "delivery_method": "home"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]

        assert data["status"] == "pending"
        assert data["delivery_method"] == "home"
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == "prod_001"
        assert data["items"][0]["quantity"] == 2

        # Verify totals
        unit_price = float(data["items"][0]["unit_price"])
        qty        = data["items"][0]["quantity"]
        subtotal   = float(data["subtotal"])
        assert subtotal == round(unit_price * qty, 2)

        delivery_fee = float(data["delivery_fee"])
        assert delivery_fee == 2800.0           # home delivery fee

        tax   = float(data["tax"])
        total = float(data["total"])
        assert round(tax, 2)   == round(subtotal * 0.075, 2)
        assert round(total, 2) == round(subtotal + delivery_fee + tax, 2)

    def test_checkout_pickup_delivery(self, client):
        token = _register_and_login(client, suffix="2")
        _add_cart_item(client, token)

        resp = client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "pickup"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert float(resp.json()["data"]["delivery_fee"]) == 1500.0

    def test_checkout_clears_cart(self, client):
        token = _register_and_login(client, suffix="3")
        _add_cart_item(client, token)
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "home"},
            headers=headers,
        )

        cart_resp = client.get("/api/v1/cart/", headers=headers)
        assert cart_resp.json()["data"]["items"] == []

    def test_checkout_empty_cart_returns_400(self, client):
        token = _register_and_login(client, suffix="4")
        resp  = client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "home"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert "empty" in resp.json()["message"].lower()

    def test_checkout_invalid_address_returns_404(self, client):
        token = _register_and_login(client, suffix="5")
        _add_cart_item(client, token)

        resp = client.post(
            "/api/v1/orders/checkout",
            json={"address_id": "nonexistent-address-id", "delivery_method": "home"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_checkout_with_promo_code(self, client):
        token = _register_and_login(client, suffix="6")
        _add_cart_item(client, token)

        resp = client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "home", "promo_code": "W2EZ2Y"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert float(data["promo_discount"]) == 1500.0
        assert data["promo_code"] == "W2EZ2Y"

    def test_checkout_invalid_delivery_method_returns_422(self, client):
        token = _register_and_login(client, suffix="7")
        _add_cart_item(client, token)

        resp = client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "teleport"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


# ── Promo tests ────────────────────────────────────────────────

class TestPromo:
    def test_valid_promo_code(self, client):
        token = _register_and_login(client, suffix="p1")
        resp  = client.post(
            "/api/v1/orders/apply-promo",
            json={"code": "W2EZ2Y"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert float(resp.json()["data"]["discount"]) == 1500.0

    def test_invalid_promo_code_returns_400(self, client):
        token = _register_and_login(client, suffix="p2")
        resp  = client.post(
            "/api/v1/orders/apply-promo",
            json={"code": "BADCODE"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400


# ── List / Get order tests ─────────────────────────────────────

class TestGetOrders:
    def _place_order(self, client, token):
        _add_cart_item(client, token)
        return client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "home"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()["data"]

    def test_list_orders_empty(self, client):
        token = _register_and_login(client, suffix="lo1")
        resp  = client.get("/api/v1/orders/", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0

    def test_list_orders_returns_placed_orders(self, client):
        token = _register_and_login(client, suffix="lo2")
        self._place_order(client, token)
        resp = client.get("/api/v1/orders/", headers={"Authorization": f"Bearer {token}"})
        assert resp.json()["data"]["total"] == 1

    def test_get_order_by_id(self, client):
        token    = _register_and_login(client, suffix="go1")
        order    = self._place_order(client, token)
        order_id = order["id"]

        resp = client.get(f"/api/v1/orders/{order_id}",
                          headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == order_id

    def test_get_other_users_order_returns_404(self, client):
        token_a  = _register_and_login(client, suffix="oa1")
        order    = self._place_order(client, token_a)
        order_id = order["id"]

        token_b  = _register_and_login(client, suffix="oa2")
        resp     = client.get(f"/api/v1/orders/{order_id}",
                              headers={"Authorization": f"Bearer {token_b}"})
        assert resp.status_code == 404


# ── Status transition tests ────────────────────────────────────

class TestOrderStatus:
    def _place_order(self, client, token):
        _add_cart_item(client, token)
        return client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "home"},
            headers={"Authorization": f"Bearer {token}"},
        ).json()["data"]

    def test_pending_to_processing(self, client):
        token    = _register_and_login(client, suffix="st1")
        order    = self._place_order(client, token)
        order_id = order["id"]

        resp = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "processing"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "processing"

    def test_pending_to_cancelled(self, client):
        token    = _register_and_login(client, suffix="st2")
        order    = self._place_order(client, token)
        order_id = order["id"]

        resp = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "cancelled"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "cancelled"

    def test_completed_to_pending_returns_400(self, client):
        """Terminal status — no further transitions allowed."""
        token    = _register_and_login(client, suffix="st3")
        order    = self._place_order(client, token)
        order_id = order["id"]
        headers  = {"Authorization": f"Bearer {token}"}

        client.patch(f"/api/v1/orders/{order_id}/status",
                     json={"status": "processing"}, headers=headers)
        client.patch(f"/api/v1/orders/{order_id}/status",
                     json={"status": "completed"}, headers=headers)

        resp = client.patch(f"/api/v1/orders/{order_id}/status",
                            json={"status": "processing"}, headers=headers)
        assert resp.status_code == 400

    def test_invalid_transition_returns_400(self, client):
        token    = _register_and_login(client, suffix="st4")
        order    = self._place_order(client, token)
        order_id = order["id"]

        resp = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "completed"},   # pending → completed is not allowed
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400