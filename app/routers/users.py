from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Review, Listing
from app.schemas import (
    UserUpdate,
    User as UserSchema,
    UserProfile,
    Review as ReviewSchema,
)
from app.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserSchema)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=UserProfile)
def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate average rating and total reviews
    avg_rating = (
        db.query(func.avg(Review.rating))
        .filter(Review.reviewed_user_id == user_id)
        .scalar()
    )
    total_reviews = db.query(Review).filter(Review.reviewed_user_id == user_id).count()
    total_listings = db.query(Listing).filter(Listing.created_by == user_id).count()

    user_profile = UserProfile(
        **user.__dict__,
        average_rating=avg_rating,
        total_reviews=total_reviews,
        total_listings=total_listings,
    )
    return user_profile


@router.get("/{user_id}/reviews", response_model=List[ReviewSchema])
def get_user_reviews(user_id: str, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.reviewed_user_id == user_id).all()
    return reviews
