"""
Initialize the database with sample data
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import (
    Base,
    User,
    Listing,
    ListingType,
    ListingStatus,
    PriceUnit,
    TradePreference,
)
from app.auth import get_password_hash
from app.utils import generate_id
import json
from datetime import datetime


def create_sample_data():
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if users already exist
        existing_user = db.query(User).first()
        if existing_user:
            print("Sample data already exists. Skipping initialization.")
            return

        print("Creating sample users...")
        # Create sample users
        users_data = [
            {
                "email": "farmer@example.com",
                "password": "password123",
                "full_name": "John Farmer",
                "bio": "Organic farmer with 10+ years experience",
                "phone": "+1-555-0101",
                "address": "123 Farm Road, Springfield, IL",
            },
            {
                "email": "gardener@example.com",
                "password": "password123",
                "full_name": "Jane Gardener",
                "bio": "Home gardener passionate about fresh vegetables",
                "phone": "+1-555-0102",
                "address": "456 Garden Lane, Madison, WI",
            },
            {
                "email": "chef@example.com",
                "password": "password123",
                "full_name": "Chef Mike",
                "bio": "Restaurant chef looking for fresh local ingredients",
                "phone": "+1-555-0103",
                "address": "789 Culinary St, Chicago, IL",
            },
        ]

        created_users = []
        for user_data in users_data:
            user = User(
                id=generate_id(),
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=get_password_hash(user_data["password"]),
                bio=user_data["bio"],
                phone=user_data["phone"],
                address=user_data["address"],
            )
            db.add(user)
            created_users.append(user)

        db.commit()
        print(f"Created {len(created_users)} users.")

        print("Creating sample listings...")
        # Create sample listings
        listings_data = [
            {
                "title": "Fresh Organic Tomatoes",
                "description": "Vine-ripened heirloom tomatoes from our organic farm. Perfect for salads and cooking.",
                "category": "tomatoes_peppers",
                "listing_type": ListingType.for_sale,
                "price": 4.50,
                "price_unit": PriceUnit.per_lb,
                "quantity_available": "20 lbs available",
                "trade_preference": TradePreference.both,
                "images": [
                    "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=500"
                ],
                "organic": True,
                "location": {
                    "city": "Springfield",
                    "state": "IL",
                    "latitude": 39.7817,
                    "longitude": -89.6501,
                },
                "created_by": created_users[0].id,
            },
            {
                "title": "Fresh Basil Leaves",
                "description": "Aromatic sweet basil, perfect for pesto and Italian cooking.",
                "category": "herbs",
                "listing_type": ListingType.for_sale,
                "price": 3.00,
                "price_unit": PriceUnit.per_bag,
                "quantity_available": "10 bags available",
                "trade_preference": TradePreference.both,
                "images": [
                    "https://images.unsplash.com/photo-1618375569909-3c8616cf5ecf?w=500"
                ],
                "organic": True,
                "location": {
                    "city": "Madison",
                    "state": "WI",
                    "latitude": 43.0731,
                    "longitude": -89.4012,
                },
                "created_by": created_users[1].id,
            },
            {
                "title": "Looking for Fresh Strawberries",
                "description": "Restaurant looking for 10+ lbs of fresh strawberries for our dessert menu.",
                "category": "berries",
                "listing_type": ListingType.looking_for,
                "quantity_available": "10+ lbs needed",
                "trade_preference": TradePreference.sale_only,
                "location": {
                    "city": "Chicago",
                    "state": "IL",
                    "latitude": 41.8781,
                    "longitude": -87.6298,
                },
                "created_by": created_users[2].id,
            },
        ]

        for listing_data in listings_data:
            listing = Listing(
                id=generate_id(),
                **listing_data,
                status=ListingStatus.active,
                view_count=0,
            )
            db.add(listing)

        db.commit()
        print(f"Created {len(listings_data)} sample listings.")
        print("Sample data created successfully!")

        # Print login credentials
        print("\n" + "=" * 50)
        print("TEST LOGIN CREDENTIALS:")
        print("=" * 50)
        print("Email: farmer@example.com")
        print("Password: password123")
        print("=" * 50)

    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
