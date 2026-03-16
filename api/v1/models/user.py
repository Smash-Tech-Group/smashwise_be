from sqlalchemy import Column, String, Boolean
from api.v1.models.base_model import BaseTableModel

class User(BaseTableModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
