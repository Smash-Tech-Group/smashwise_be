from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel

class Cart(BaseTableModel):
    __tablename__ = "carts"
    
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    user = relationship("User", backref="cart")

class CartItem(BaseTableModel):
    __tablename__ = "cart_items"
    
    cart_id = Column(String, ForeignKey("carts.id"), nullable=False)
    product_id = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    product_image = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    
    cart = relationship("Cart", back_populates="items")
