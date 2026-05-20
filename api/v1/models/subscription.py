"""
api/v1/models/subscription.py

Newsletter subscription model.
Stores unique email addresses for the footer subscribe feature.
One record per email — duplicate attempts are rejected at the service layer.
"""

from sqlalchemy import Column, String
from api.v1.models.base_model import BaseTableModel


class Subscription(BaseTableModel):
    __tablename__ = "subscriptions"

    email = Column(String, unique=True, nullable=False, index=True)