"""
api/v1/models/address.py

UserAddress model — stores delivery addresses for each user.
One address per user can be marked as is_default=True.
Enforcement of the single-default constraint is handled in address_service.py.
"""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from api.v1.models.base_model import BaseTableModel


class UserAddress(BaseTableModel):
    __tablename__ = "user_addresses"

    user_id        = Column(String, ForeignKey("users.id"),  nullable=False, index=True)
    category       = Column(String, nullable=False)   # home | work | gym | church | school | custom
    name           = Column(String, nullable=False)   # "Home", "Office", …
    contact_person = Column(String, nullable=False)
    address        = Column(String, nullable=False)
    is_default     = Column(Boolean, default=False, nullable=False)

    user   = relationship("User",  backref="addresses")