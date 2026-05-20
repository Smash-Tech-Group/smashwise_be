"""
api/v1/models/__init__.py

Import all models here so Alembic autogenerate can discover every table.

Added in feat/profile-footer-auth-routing:
  Subscription — newsletter subscriber emails
"""

from api.v1.models.base_model    import BaseTableModel                         # noqa: F401
from api.v1.models.user          import User                                   # noqa: F401
from api.v1.models.cart          import Cart, CartItem                         # noqa: F401
from api.v1.models.address       import UserAddress                            # noqa: F401
from api.v1.models.order         import Order, OrderItem                       # noqa: F401
from api.v1.models.payment       import Payment                                # noqa: F401
from api.v1.models.product       import Product, ProductImage, ProductReview   # noqa: F401
from api.v1.models.wishlist      import WishlistItem                           # noqa: F401
from api.v1.models.subscription  import Subscription                           # noqa: F401