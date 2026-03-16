from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from api.db.database import get_db
from api.utils.success_response import success_response
from api.utils.jwt_handler import get_current_user
from api.v1.models.user import User
from api.v1.schemas.cart import CartItemAdd, CartItemUpdate
from api.v1.services.cart_service import cart_service

cart = APIRouter(prefix="/cart", tags=["Cart"])

@cart.get("/", status_code=status.HTTP_200_OK)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = cart_service.get_cart(db, user)
    return success_response(status_code=200, message="Cart retrieved", data=data)

@cart.post("/items", status_code=status.HTTP_200_OK)
def add_item(request: CartItemAdd, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = cart_service.add_item(db, user, request)
    return success_response(status_code=200, message="Item added", data=data)

@cart.patch("/items/{item_id}", status_code=status.HTTP_200_OK)
def update_item(item_id: str, request: CartItemUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = cart_service.update_item(db, user, item_id, request)
    return success_response(status_code=200, message="Item updated", data=data)

@cart.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
def remove_item(item_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = cart_service.remove_item(db, user, item_id)
    return success_response(status_code=200, message="Item removed", data=data)

@cart.delete("/", status_code=status.HTTP_200_OK)
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = cart_service.clear_cart(db, user)
    return success_response(status_code=200, message="Cart cleared", data=data)
