from sqlalchemy.orm import Session
from fastapi import HTTPException
from api.core.base.services import Service
from api.v1.models.cart import Cart, CartItem
from api.v1.models.user import User
from api.v1.schemas.cart import CartItemAdd, CartItemUpdate

class CartService(Service):
    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    def get_cart(self, db: Session, user: User):
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            cart = Cart(user_id=user.id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        
        items_out = []
        total_price = 0.0
        for item in cart.items:
            items_out.append(item.to_dict())
            total_price += item.price * item.quantity
        
        cart_data = cart.to_dict()
        cart_data["items"] = items_out
        cart_data["total_price"] = total_price
        
        return cart_data

    def add_item(self, db: Session, user: User, data: CartItemAdd):
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            cart = Cart(user_id=user.id)
            db.add(cart)
            db.flush()
            
        item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == data.product_id).first()
        if item:
            item.quantity += data.quantity
        else:
            item = CartItem(
                cart_id=cart.id,
                product_id=data.product_id,
                product_name=data.product_name,
                product_image=data.product_image,
                price=data.price,
                quantity=data.quantity
            )
            db.add(item)
            
        db.commit()
        return self.get_cart(db, user)

    def update_item(self, db: Session, user: User, item_id: str, data: CartItemUpdate):
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
            
        item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")
            
        if data.quantity <= 0:
            db.delete(item)
        else:
            item.quantity = data.quantity
            
        db.commit()
        return self.get_cart(db, user)

    def remove_item(self, db: Session, user: User, item_id: str):
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")
            
        item = db.query(CartItem).filter(CartItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        if item.cart_id != cart.id:
            raise HTTPException(status_code=403, detail="Item does not belong to your cart")
            
        db.delete(item)
        db.commit()
        return self.get_cart(db, user)

    def clear_cart(self, db: Session, user: User):
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            return {"id": "", "user_id": user.id, "items": [], "total_price": 0.0, "updated_at": ""}
            
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()
        return self.get_cart(db, user)

cart_service = CartService()
