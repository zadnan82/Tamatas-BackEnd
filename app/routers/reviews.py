from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Review, Listing
from app.schemas import ReviewCreate, Review as ReviewSchema
from app.auth import get_current_active_user
from app.utils import generate_id

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=ReviewSchema)
def create_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Check if user exists
    reviewed_user = db.query(User).filter(User.id == review.reviewed_user_id).first()
    if not reviewed_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is trying to review themselves
    if review.reviewed_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    # Check if review already exists for this user-listing combination
    existing_review = (
        db.query(Review)
        .filter(
            Review.reviewer_id == current_user.id,
            Review.reviewed_user_id == review.reviewed_user_id,
            Review.listing_id == review.listing_id,
        )
        .first()
    )

    if existing_review:
        raise HTTPException(
            status_code=400, detail="Review already exists for this listing"
        )

    db_review = Review(id=generate_id(), reviewer_id=current_user.id, **review.dict())
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@router.get("/user/{user_id}", response_model=List[ReviewSchema])
def get_user_reviews(user_id: str, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.reviewed_user_id == user_id).all()
    return reviews
