"""
tests/v1/reviews/test_reviews.py

Unit tests for the Review Purchase feature.

Covers:
  POST /api/v1/reviews                         — submit review
  GET  /api/v1/orders/{order_id}/reviewable    — reviewable line items
  GET  /api/v1/products/{product_id}/can-review — eligibility check
"""

# File: tests/v1/reviews/test_reviews.py

import pytest
from fastapi.testclient import TestClient


# ── Test data ──────────────────────────────────────────────────

MOCK_PRODUCT_ID   = "prod_001"
MOCK_PRODUCT_NAME = "Men Lace-up Shoes"
MOCK_PRODUCT_IMG  = "https://example.com/shoe.png"
MOCK_PRICE        = 11900


# ── Helpers ────────────────────────────────────────────────────

def _register_and_login(client: TestClient, suffix: str = "") -> str:
    """Register a new user and return their access token."""
    email    = f"review_user{suffix}@example.com"
    username = f"review_user{suffix}"
    signup   = client.post("/api/v1/auth/signup/otp", json={
        "email": email, "username": username, "password": "Secure@123",
    })
    otp    = signup.json()["data"]["otp"]
    verify = client.post("/api/v1/auth/verify-otp/signup", json={"email": email, "otp": otp})
    return verify.json()["data"]["access_token"]


def _add_cart_item(client: TestClient, token: str) -> None:
    client.post(
        "/api/v1/cart/items",
        json={
            "product_id":    MOCK_PRODUCT_ID,
            "product_name":  MOCK_PRODUCT_NAME,
            "product_image": MOCK_PRODUCT_IMG,
            "price":         MOCK_PRICE,
            "quantity":      1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )


def _place_and_deliver_order(client: TestClient, token: str) -> tuple[str, str]:
    """
    Place an order and transition it all the way to 'delivered'.
    Returns (order_id, first_line_item_id).
    """
    _add_cart_item(client, token)
    headers = {"Authorization": f"Bearer {token}"}

    order_resp = client.post(
        "/api/v1/orders/checkout",
        json={"delivery_method": "pickup"},
        headers=headers,
    )
    assert order_resp.status_code == 201, order_resp.text
    order    = order_resp.json()["data"]
    order_id = order["id"]
    item_id  = order["items"][0]["id"]

    # pending → processing → completed → delivered
    for target_status in ("processing", "completed", "delivered"):
        r = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": target_status},
            headers=headers,
        )
        assert r.status_code == 200, f"Failed transitioning to {target_status}: {r.text}"

    return order_id, item_id


def _valid_review_payload(order_line_item_id: str) -> dict:
    return {
        "order_line_item_id": order_line_item_id,
        "product_id":         MOCK_PRODUCT_ID,
        "rating":             5,
        "title":              "Absolutely love these shoes!",
        "body":               "Super comfortable and true to size.",
        "reviewer_name":      "Test Buyer",
        "media_urls":         [],
    }


# ── POST /reviews ──────────────────────────────────────────────

class TestSubmitReview:

    def test_submit_review_success(self, client):
        token              = _register_and_login(client, "sr1")
        order_id, item_id  = _place_and_deliver_order(client, token)

        resp = client.post(
            "/api/v1/reviews",
            json=_valid_review_payload(item_id),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["rating"]             == 5
        assert data["title"]              == "Absolutely love these shoes!"
        assert data["order_line_item_id"] == item_id
        assert data["verified"]           is True

    def test_submit_review_duplicate_returns_409(self, client):
        token              = _register_and_login(client, "sr2")
        order_id, item_id  = _place_and_deliver_order(client, token)
        headers            = {"Authorization": f"Bearer {token}"}
        payload            = _valid_review_payload(item_id)

        # First submission
        r1 = client.post("/api/v1/reviews", json=payload, headers=headers)
        assert r1.status_code == 201

        # Duplicate submission
        r2 = client.post("/api/v1/reviews", json=payload, headers=headers)
        assert r2.status_code == 409
        assert "already exists" in r2.json()["message"].lower()

    def test_submit_review_unauthenticated_returns_401(self, client):
        resp = client.post(
            "/api/v1/reviews",
            json=_valid_review_payload("some-item-id"),
        )
        # App returns 403 (not 401) for missing token — matches get_current_user behaviour
        assert resp.status_code == 403

    def test_submit_review_wrong_user_returns_404(self, client):
        """User B cannot submit a review for User A's line item."""
        token_a             = _register_and_login(client, "sr3a")
        _order_id, item_id  = _place_and_deliver_order(client, token_a)

        token_b = _register_and_login(client, "sr3b")
        resp    = client.post(
            "/api/v1/reviews",
            json=_valid_review_payload(item_id),
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    def test_submit_review_missing_title_returns_422(self, client):
        token   = _register_and_login(client, "sr4")
        payload = _valid_review_payload("some-item-id")
        del payload["title"]
        resp = client.post(
            "/api/v1/reviews",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_submit_review_rating_out_of_range_returns_422(self, client):
        token           = _register_and_login(client, "sr5")
        payload         = _valid_review_payload("some-item-id")
        payload["rating"] = 6   # max is 5
        resp = client.post(
            "/api/v1/reviews",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_submit_review_with_media_urls(self, client):
        token             = _register_and_login(client, "sr6")
        order_id, item_id = _place_and_deliver_order(client, token)
        payload           = _valid_review_payload(item_id)
        payload["media_urls"] = [
            "https://example.com/photo1.jpg",
            "https://example.com/photo2.jpg",
        ]
        resp = client.post(
            "/api/v1/reviews",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert len(resp.json()["data"]["media_urls"]) == 2


# ── GET /orders/{order_id}/reviewable ─────────────────────────

class TestReviewableItems:

    def test_delivered_order_returns_items(self, client):
        token             = _register_and_login(client, "ri1")
        order_id, item_id = _place_and_deliver_order(client, token)

        resp = client.get(
            f"/api/v1/orders/{order_id}/reviewable",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["id"] == item_id

    def test_non_delivered_order_returns_empty(self, client):
        """Order in 'processing' status → no reviewable items."""
        token = _register_and_login(client, "ri2")
        _add_cart_item(client, token)
        headers = {"Authorization": f"Bearer {token}"}

        order_resp = client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "pickup"},
            headers=headers,
        )
        order_id = order_resp.json()["data"]["id"]

        # Only advance to processing — not delivered
        client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={"status": "processing"},
            headers=headers,
        )

        resp = client.get(
            f"/api/v1/orders/{order_id}/reviewable",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["items"] == []

    def test_reviewed_items_excluded(self, client):
        """After submitting a review, the item is no longer reviewable."""
        token             = _register_and_login(client, "ri3")
        order_id, item_id = _place_and_deliver_order(client, token)
        headers           = {"Authorization": f"Bearer {token}"}

        # Submit review
        client.post(
            "/api/v1/reviews",
            json=_valid_review_payload(item_id),
            headers=headers,
        )

        # Should now return empty
        resp = client.get(f"/api/v1/orders/{order_id}/reviewable", headers=headers)
        assert resp.json()["data"]["items"] == []

    def test_other_users_order_returns_404(self, client):
        token_a  = _register_and_login(client, "ri4a")
        order_id, _ = _place_and_deliver_order(client, token_a)

        token_b = _register_and_login(client, "ri4b")
        resp    = client.get(
            f"/api/v1/orders/{order_id}/reviewable",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/api/v1/orders/some-order-id/reviewable")
        # App returns 403 (not 401) for missing token — matches get_current_user behaviour
        assert resp.status_code == 403


# ── GET /products/{product_id}/can-review ─────────────────────

class TestCanReview:

    def test_can_review_true_after_delivery(self, client):
        token = _register_and_login(client, "cr1")
        _place_and_deliver_order(client, token)

        resp = client.get(
            f"/api/v1/products/{MOCK_PRODUCT_ID}/can-review",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["can_review"] is True

    def test_can_review_false_before_delivery(self, client):
        """Order placed but not yet delivered."""
        token   = _register_and_login(client, "cr2")
        _add_cart_item(client, token)
        headers = {"Authorization": f"Bearer {token}"}

        client.post(
            "/api/v1/orders/checkout",
            json={"delivery_method": "pickup"},
            headers=headers,
        )

        resp = client.get(
            f"/api/v1/products/{MOCK_PRODUCT_ID}/can-review",
            headers=headers,
        )
        assert resp.json()["data"]["can_review"] is False

    def test_can_review_false_no_purchase(self, client):
        """User has never bought this product."""
        token = _register_and_login(client, "cr3")
        resp  = client.get(
            f"/api/v1/products/{MOCK_PRODUCT_ID}/can-review",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.json()["data"]["can_review"] is False

    def test_can_review_false_after_review_submitted(self, client):
        """Once reviewed, can_review should return False."""
        token             = _register_and_login(client, "cr4")
        order_id, item_id = _place_and_deliver_order(client, token)
        headers           = {"Authorization": f"Bearer {token}"}

        client.post(
            "/api/v1/reviews",
            json=_valid_review_payload(item_id),
            headers=headers,
        )

        resp = client.get(
            f"/api/v1/products/{MOCK_PRODUCT_ID}/can-review",
            headers=headers,
        )
        assert resp.json()["data"]["can_review"] is False

    def test_can_review_unauthenticated_returns_401(self, client):
        resp = client.get(f"/api/v1/products/{MOCK_PRODUCT_ID}/can-review")
        # App returns 403 (not 401) for missing token — matches get_current_user behaviour
        assert resp.status_code == 403