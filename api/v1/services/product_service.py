"""
api/v1/services/product_service.py

Business logic for Product, ProductImage, and ProductReview CRUD.
Includes a seed function to populate initial products from mock data.
"""

from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from api.core.base.services import Service
from api.v1.models.product import Product, ProductImage, ProductReview
from api.v1.models.user import User
from api.v1.schemas.product import ProductCreate, ProductUpdate, ReviewCreate


class ProductService(Service):
    # ── Abstract stubs ─────────────────────────────────────────
    def create(self): pass
    def fetch(self): pass
    def fetch_all(self): pass
    def update(self): pass
    def delete(self): pass

    # ── Queries ────────────────────────────────────────────────

    def get_products(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        category: str = None,
        search: str = None,
    ):
        query = db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
        total = query.count()
        products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
        return total, products

    def get_product(self, db: Session, product_id: str) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )
        return product

    def get_reviews(self, db: Session, product_id: str) -> list[ProductReview]:
        # Ensure product exists
        self.get_product(db, product_id)
        return (
            db.query(ProductReview)
            .filter(ProductReview.product_id == product_id)
            .order_by(ProductReview.created_at.desc())
            .all()
        )

    def create_review(
        self, db: Session, user: User, product_id: str, data: ReviewCreate
    ) -> ProductReview:
        # Ensure product exists
        product = self.get_product(db, product_id)

        review = ProductReview(
            product_id=product_id,
            user_id=user.id,
            reviewer_name=user.full_name or user.username,
            title=data.comment[:100] if data.comment else f"{data.rating}-star review",  # fallback title for legacy endpoint
            rating=data.rating,
            comment=data.comment,
            verified=True,
        )
        db.add(review)

        # Update product rating and review count
        product.review_count += 1
        all_reviews = (
            db.query(ProductReview)
            .filter(ProductReview.product_id == product_id)
            .all()
        )
        total_rating = sum(r.rating for r in all_reviews) + data.rating
        product.rating = round(total_rating / (len(all_reviews) + 1), 1)

        db.commit()
        db.refresh(review)
        return review

    def get_rating_breakdown(self, db: Session, product_id: str) -> dict:
        self.get_product(db, product_id)
        result = {}
        for star in range(1, 6):
            count = (
                db.query(ProductReview)
                .filter(
                    ProductReview.product_id == product_id,
                    ProductReview.rating == star,
                )
                .count()
            )
            result[star] = count
        return result

    def get_recommended(self, db: Session, product_id: str, limit: int = 5):
        """Return products in the same category, excluding the current one."""
        product = self.get_product(db, product_id)
        query = db.query(Product).filter(Product.id != product_id)
        if product.category:
            query = query.filter(Product.category == product.category)
        products = query.order_by(func.random()).limit(limit).all()
        # Fallback: if not enough in same category, fill with random
        if len(products) < limit:
            remaining = limit - len(products)
            existing_ids = [p.id for p in products] + [product_id]
            extras = (
                db.query(Product)
                .filter(Product.id.notin_(existing_ids))
                .order_by(func.random())
                .limit(remaining)
                .all()
            )
            products.extend(extras)
        return products

    # ── Admin: create product ──────────────────────────────────

    def create_product(self, db: Session, data: ProductCreate) -> Product:
        product = Product(
            name=data.name,
            description=data.description,
            price=data.price,
            old_price=data.old_price,
            badge=data.badge,
            stock_status=data.stock_status,
            category=data.category,
            vendor=data.vendor,
            specifications=data.specifications,
            sizes=data.sizes,
            colors=data.colors,
            delivery_info=data.delivery_info,
        )
        db.add(product)
        db.flush()

        if data.images:
            for i, url in enumerate(data.images):
                img = ProductImage(product_id=product.id, url=url, sort_order=i)
                db.add(img)

        db.commit()
        db.refresh(product)
        return product

    # ── Seed mock products ─────────────────────────────────────

    def seed_products(self, db: Session) -> list[Product]:
        """Seed the database with initial mock products. Idempotent."""
        existing = db.query(Product).count()
        if existing > 0:
            return db.query(Product).all()

        mock_products = [
            {
                "name": "Men's Lace-up Trendy Sketch Shoes for Men — Multicolour Graffiti Canvas Sneakers",
                "description": "Have you ever had the saying 'the right pair of shoes can help you conquer all'? Well, your search is at an end because these pairs of shoes are a classic pair of shoes made with the finest material.",
                "price": Decimal("11900.00"),
                "old_price": Decimal("19500.00"),
                "badge": "25% OFF",
                "stock_status": "in_stock",
                "rating": 4.1,
                "review_count": 6,
                "category": "sneakers",
                "vendor": "SmashWise Fashion Store",
                "specifications": {
                    "Brand": "SmashWise Fashion",
                    "Upper Material": "Polyester Canvas",
                    "Sole Material": "Synthetic Rubber",
                    "Closure": "Lace-up",
                    "Style": "Casual / Sneaker",
                    "Gender": "Men",
                    "Pattern": "Graffiti / Multicolour",
                    "Care": "Wipe with damp cloth",
                    "Warranty": "30-day return guarantee",
                },
                "sizes": [40, 42, 44, 47],
                "colors": [
                    {"name": "Black", "hex": "#1a1a1a"},
                    {"name": "White", "hex": "#F5F5F5"},
                    {"name": "Red",   "hex": "#EF4444"},
                ],
                "delivery_info": {
                    "delivery": "2–5 business days nationwide",
                    "return_policy": "7-day hassle-free return policy",
                    "warranty_policy": "30-day manufacturer guarantee included",
                },
                "images": [
                    "/media/products/shoe1.png",
                    "/media/products/shoe2.png",
                    "/media/products/shoe3.png",
                    "/media/products/shoe4.png",
                ],
            },
            {
                "name": "Men Shoes Sneakers Casual Sport Running",
                "description": "Lightweight and breathable sport running sneakers perfect for everyday wear.",
                "price": Decimal("11900.00"),
                "old_price": None,
                "badge": "NEW",
                "stock_status": "in_stock",
                "rating": 4.0,
                "review_count": 83,
                "category": "sneakers",
                "vendor": "SmashWise Fashion Store",
                "specifications": {"Brand": "SmashWise", "Style": "Sport"},
                "sizes": [40, 42, 44, 46],
                "colors": [{"name": "Black", "hex": "#1a1a1a"}],
                "delivery_info": {"delivery": "2–5 business days"},
                "images": ["/media/products/rec1.png"],
            },
            {
                "name": "EAGEAT Unisex Lightweight Gym Shoes",
                "description": "Ultra-lightweight gym shoes designed for performance and comfort.",
                "price": Decimal("8400.00"),
                "old_price": None,
                "badge": None,
                "stock_status": "in_stock",
                "rating": 4.0,
                "review_count": 23,
                "category": "sneakers",
                "vendor": "SmashWise Fashion Store",
                "specifications": {"Brand": "EAGEAT", "Style": "Gym"},
                "sizes": [38, 40, 42, 44],
                "colors": [{"name": "Grey", "hex": "#9CA3AF"}],
                "delivery_info": {"delivery": "2–5 business days"},
                "images": ["/media/products/rec2.png"],
            },
            {
                "name": "Nike Air Force 1 Low White",
                "description": "The iconic Nike Air Force 1 Low in classic white.",
                "price": Decimal("31500.00"),
                "old_price": Decimal("35000.00"),
                "badge": "10% OFF",
                "stock_status": "in_stock",
                "rating": 4.0,
                "review_count": 56,
                "category": "sneakers",
                "vendor": "SmashWise Fashion Store",
                "specifications": {"Brand": "Nike", "Style": "Casual"},
                "sizes": [40, 42, 44, 46],
                "colors": [{"name": "White", "hex": "#F5F5F5"}],
                "delivery_info": {"delivery": "2–5 business days"},
                "images": ["/media/products/rec3.png"],
            },
            {
                "name": "Adidas Ultraboost Running Shoe",
                "description": "Premium running shoe with Boost cushioning technology.",
                "price": Decimal("27800.00"),
                "old_price": None,
                "badge": "NEW",
                "stock_status": "in_stock",
                "rating": 5.0,
                "review_count": 211,
                "category": "sneakers",
                "vendor": "SmashWise Fashion Store",
                "specifications": {"Brand": "Adidas", "Style": "Running"},
                "sizes": [40, 42, 44, 46],
                "colors": [{"name": "Black", "hex": "#1a1a1a"}],
                "delivery_info": {"delivery": "2–5 business days"},
                "images": ["/media/products/rec4.png"],
            },
            {
                "name": "Classic Canvas Low-Top Sneaker",
                "description": "Timeless canvas low-top sneaker for everyday casual wear.",
                "price": Decimal("7200.00"),
                "old_price": None,
                "badge": None,
                "stock_status": "in_stock",
                "rating": 4.0,
                "review_count": 93,
                "category": "sneakers",
                "vendor": "SmashWise Fashion Store",
                "specifications": {"Brand": "SmashWise", "Style": "Casual"},
                "sizes": [38, 40, 42, 44, 46],
                "colors": [{"name": "Canvas", "hex": "#D4C5A9"}],
                "delivery_info": {"delivery": "2–5 business days"},
                "images": ["/media/products/rec5.png"],
            },
        ]

        created = []
        for mp in mock_products:
            images = mp.pop("images", [])
            product = Product(**mp)
            db.add(product)
            db.flush()

            for i, url in enumerate(images):
                img = ProductImage(product_id=product.id, url=url, sort_order=i)
                db.add(img)

            created.append(product)

        # Seed reviews for the first product
        mock_reviews = [
            {"reviewer_name": "John Nwadike",   "title": "Great value for money",          "rating": 5, "comment": "Great value for money",                                       "verified": True},
            {"reviewer_name": "Sarah M.",        "title": "Highly recommended!",            "rating": 5, "comment": "Love the quality and performance. Highly recommended!",        "verified": True},
            {"reviewer_name": "Tunde Balogun",  "title": "Well packaged and nice",         "rating": 4, "comment": "Very nice sneakers, came well packaged.",                      "verified": True},
            {"reviewer_name": "Amaka O.",        "title": "Perfect gift",                   "rating": 4, "comment": "Bought this for my boyfriend and he absolutely loves it.",     "verified": True},
            {"reviewer_name": "Chukwuemeka D.", "title": "Good but runs small",            "rating": 3, "comment": "Decent shoe for the price. Runs slightly small.",              "verified": True},
            {"reviewer_name": "Fatima A.",       "title": "Exceeded my expectations!",      "rating": 5, "comment": "Exceeded my expectations! The design is gorgeous.",           "verified": True},
        ]
        for mr in mock_reviews:
            review = ProductReview(product_id=created[0].id, **mr)
            db.add(review)

        db.commit()
        for p in created:
            db.refresh(p)
        return created


product_service = ProductService()