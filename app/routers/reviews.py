from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
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
    # Validate reviewed user exists
    reviewed_user = db.query(User).filter(User.id == review.reviewed_user_id).first()
    if not reviewed_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-reviews
    if review.reviewed_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    # Check for existing review
    existing_query = db.query(Review).filter(
        Review.reviewer_id == current_user.id,
        Review.reviewed_user_id == review.reviewed_user_id,
    )

    if review.listing_id:
        existing_query = existing_query.filter(Review.listing_id == review.listing_id)
    else:
        existing_query = existing_query.filter(Review.listing_id.is_(None))

    if existing_query.first():
        raise HTTPException(status_code=400, detail="Review already exists")

    # Create the review with anonymity handling
    review_data = review.dict()
    review_data.update(
        {
            "id": generate_id(),
            "reviewer_id": current_user.id,
            "show_reviewer": not review.is_anonymous,  # Hide if anonymous
        }
    )

    db_review = Review(**review_data)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Only include reviewer info if not anonymous
    if not review.is_anonymous:
        db.refresh(db_review)
        db_review.reviewer = current_user
    else:
        db_review.reviewer = None

    return db_review


@router.get("/user/{user_id}", response_model=List[ReviewSchema])
def get_user_reviews(
    user_id: str,
    db: Session = Depends(get_db),
    include_anonymous: bool = False,  # New parameter
):
    query = db.query(Review).filter(Review.reviewed_user_id == user_id)

    if not include_anonymous:
        query = query.filter(Review.show_reviewer == True)

    reviews = query.options(joinedload(Review.reviewer)).all()

    # Hide reviewer info for anonymous reviews
    for review in reviews:
        if not review.show_reviewer:
            review.reviewer = None

    return reviews
