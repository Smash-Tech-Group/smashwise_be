from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CartItemAdd(BaseModel):
    product_id: str
    product_name: str
    product_image: Optional[str] = None
    price: float
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0)

class CartItemOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    product_image: Optional[str] = None
    price: float
    quantity: int

    class Config:
        from_attributes = True

class CartOut(BaseModel):
    id: str
    user_id: str
    items: List[CartItemOut]
    total_price: float
    updated_at: datetime

    class Config:
        from_attributes = True
