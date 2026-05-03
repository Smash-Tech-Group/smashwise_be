"""
api/v1/routes/__init__.py

Registers all v1 routers under /api/v1.
"""

from fastapi import APIRouter

from api.v1.routes.auth_route    import auth
from api.v1.routes.cart_route    import cart
from api.v1.routes.address_route import address
from api.v1.routes.order_route   import order
from api.v1.routes.payment_route import payment
from api.v1.routes.profile_route import profile

api_version_one = APIRouter(prefix="/api/v1")

api_version_one.include_router(auth)
api_version_one.include_router(cart)
api_version_one.include_router(address)
api_version_one.include_router(order)
api_version_one.include_router(payment)
api_version_one.include_router(profile)