"""
api/v1/models/user.py

User model.

Fields added by feat/profile-api:
  full_name  — display name (nullable)
  phone      — contact number (nullable)
  avatar_url — profile picture URL (nullable, reserved for future upload feature)
"""

from sqlalchemy import Column, String, Boolean
from api.v1.models.base_model import BaseTableModel


class User(BaseTableModel):
    __tablename__ = "users"

    email           = Column(String, unique=True, index=True, nullable=False)
    username        = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active       = Column(Boolean, default=True)

    # ── Profile fields (added by feat/profile-api) ─────────────
    full_name  = Column(String, nullable=True)
    phone      = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)