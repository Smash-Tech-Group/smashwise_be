"""
api/v1/services/order_service.py

Business logic for the checkout flow and order lifecycle.

Checkout flow:
  1. Validate cart is not empty.
  2. Validate address ownership (if provided).
  3. Snapshot cart items into OrderItem rows (price fixed at checkout time).
  4. Compute subtotal, delivery_fee, tax, promo_discount, total.
  5. Create Order + Payment(status=pending) records.
  6. Clear the user's cart.
  7. Return the new Order.

Delivery fees and tax rate are defined as module-level constants so they
can be made DB-configurable later without touching route or schema code.
"""

from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from api.core.base.services import Service
from api.v1.models.cart import Cart, CartItem
from api.v1.models.order import Order, OrderItem, ORDER_TRANSITIONS
from api.v1.models.payment import Payment
from api.v1.models.address import UserAddress
from api.v1.models.user import User
from api.v1.schemas.order import CheckoutRequest, OrderStatusUpdate

# ── Config constants ───────────────────────────────────────────
DELIVERY_FEES: dict[str, Decimal] = {
    "home":   Decimal("2800.00"),
    "pickup": Decimal("1500.00"),
}
TAX_RATE = Decimal("0.075")   # 7.5 %

# ── Mock promo codes (replace with DB table when ready) ────────
PROMO_CODES: dict[str, dict] = {
    "W2EZ2Y":  {"discount": Decimal("1500.00"), "label": "W2EZ2Y"},
    "SAVE500": {"discount": Decimal("500.00"),  "label": "SAVE500"},
}


def _round2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class OrderService(Service):
    # ── Abstract method stubs ──────────────────────────────────
    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    # ── Promo ──────────────────────────────────────────────────

    def apply_promo(self, code: str) -> dict:
        """Validate a promo code and return discount info."""
        entry = PROMO_CODES.get(code.upper())
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired promo code.",
            )
        return {"code": code.upper(), "discount": entry["discount"], "label": entry["label"]}

    # ── Checkout ───────────────────────────────────────────────

    def checkout(self, db: Session, user: User, data: CheckoutRequest) -> Order:
        """Convert the user's active cart into an Order."""

        # 1. Fetch cart
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your cart is empty. Add items before checking out.",
            )

        # 2. Validate address
        address = None
        if data.address_id:
            address = (
                db.query(UserAddress)
                .filter(
                    UserAddress.id == data.address_id,
                    UserAddress.user_id == user.id,
                )
                .first()
            )
            if not address:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Delivery address not found or does not belong to you.",
                )

        # 3. Resolve delivery fee
        delivery_fee = DELIVERY_FEES.get(data.delivery_method, Decimal("0.00"))

        # 4. Resolve promo discount
        promo_discount = Decimal("0.00")
        promo_code_label = None
        if data.promo_code:
            entry = PROMO_CODES.get(data.promo_code.upper())
            if entry:
                promo_discount = entry["discount"]
                promo_code_label = data.promo_code.upper()

        # 5. Build OrderItems and compute subtotal
        subtotal = Decimal("0.00")
        order_items = []
        for cart_item in cart.items:
            unit_price = _round2(Decimal(str(cart_item.price)))
            item_subtotal = _round2(unit_price * cart_item.quantity)
            subtotal += item_subtotal
            order_items.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    product_name=cart_item.product_name,
                    product_image=cart_item.product_image,
                    unit_price=unit_price,
                    quantity=cart_item.quantity,
                    subtotal=item_subtotal,
                )
            )

        # 6. Compute tax and total
        tax   = _round2(subtotal * TAX_RATE)
        total = _round2(subtotal + delivery_fee + tax - promo_discount)

        # 7. Create Order
        order = Order(
            user_id=user.id,
            address_id=data.address_id,
            delivery_method=data.delivery_method,
            status="pending",
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            tax=tax,
            promo_discount=promo_discount,
            total=total,
            promo_code=promo_code_label,
        )
        db.add(order)
        db.flush()  # get order.id before adding children

        # 8. Attach OrderItems
        for oi in order_items:
            oi.order_id = order.id
            db.add(oi)

        # 9. Create Payment record (status=pending)
        payment = Payment(
            order_id=order.id,
            amount=total,
            status="pending",
            provider="paystack",
        )
        db.add(payment)

        # 10. Clear cart
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

        db.commit()
        db.refresh(order)
        return order

    # ── Queries ────────────────────────────────────────────────

    def get_order(self, db: Session, user: User, order_id: str) -> Order:
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
        return order

    def list_orders(
        self, db: Session, user: User, skip: int = 0, limit: int = 20
    ) -> tuple[int, list[Order]]:
        query = (
            db.query(Order)
            .filter(Order.user_id == user.id)
            .order_by(Order.created_at.desc())
        )
        total = query.count()
        orders = query.offset(skip).limit(limit).all()
        return total, orders

    # ── Status transitions ────────────────────────────────────

    def update_status(
        self, db: Session, user: User, order_id: str, data: OrderStatusUpdate
    ) -> Order:
        order = self.get_order(db, user, order_id)
        allowed = ORDER_TRANSITIONS.get(order.status, set())
        if data.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot transition order from '{order.status}' to '{data.status}'. "
                    f"Allowed transitions: {sorted(allowed) or 'none (terminal state)'}."
                ),
            )
        order.status = data.status
        db.commit()
        db.refresh(order)
        return order


order_service = OrderService()