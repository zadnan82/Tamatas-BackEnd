from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import User, Review, Listing
from app.schemas import ReviewCreate, Review as ReviewSchema
from app.auth import get_current_active_user
from app.utils import generate_id

router = APIRouter(prefix="/reviews", tags=["reviews"])


def validate_review_creation(review: ReviewCreate, current_user: User, db: Session):
    """Centralized validation for review creation"""
    # Validate reviewed user exists
    reviewed_user = db.query(User).filter(User.id == review.reviewed_user_id).first()
    if not reviewed_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-reviews
    if review.reviewed_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    # Prevent anonymous self-reviews (extra protection)
    if review.reviewed_user_id == current_user.id and review.is_anonymous:
        raise HTTPException(
            status_code=400, detail="Cannot leave anonymous reviews for yourself"
        )

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
        raise HTTPException(
            status_code=400, detail="Review already exists for this user/listing"
        )


@router.post("/", response_model=ReviewSchema)
def create_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    print(f"\n=== Review Creation Attempt ===")
    print(f"Current User: {current_user.id}")
    print(f"Review Data: {review.dict()}")

    try:
        # Detailed validation with logging
        print("\nValidating review...")
        reviewed_user = (
            db.query(User).filter(User.id == review.reviewed_user_id).first()
        )
        if not reviewed_user:
            error_msg = f"Reviewed user {review.reviewed_user_id} not found"
            print(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        if review.reviewed_user_id == current_user.id:
            error_msg = "User attempted to review themselves"
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        existing_review = (
            db.query(Review)
            .filter(
                Review.reviewer_id == current_user.id,
                Review.reviewed_user_id == review.reviewed_user_id,
                Review.listing_id == (review.listing_id if review.listing_id else None),
            )
            .first()
        )

        if existing_review:
            error_msg = "Duplicate review attempt"
            print(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        print("Validation passed. Creating review...")
        db_review = Review(
            id=generate_id(),
            reviewer_id=current_user.id,
            reviewed_user_id=review.reviewed_user_id,
            listing_id=review.listing_id,
            rating=review.rating,
            comment=review.comment,
            is_anonymous=review.is_anonymous,
            show_reviewer=not review.is_anonymous,
        )

        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        print(f"Review created successfully: {db_review.id}")
        return db_review

    except HTTPException as e:
        print(f"Validation error: {e.detail}")
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user/{user_id}", response_model=List[ReviewSchema])
def get_user_reviews(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    include_anonymous: bool = False,
):
    """Get reviews for a user with optional anonymous review inclusion"""
    # Allow viewing own anonymous reviews or if admin
    if current_user.id == user_id:
        include_anonymous = True

    query = db.query(Review).filter(Review.reviewed_user_id == user_id)

    if not include_anonymous:
        query = query.filter(Review.show_reviewer == True)

    reviews = query.options(joinedload(Review.reviewer)).all()

    # Hide reviewer info for anonymous reviews for non-privileged users
    if not include_anonymous:
        for review in reviews:
            if review.is_anonymous:
                review.reviewer = None

    return reviews


def validate_review_creation(review: ReviewCreate, current_user: User, db: Session):
    """Centralized validation for review creation"""
    # Validate reviewed user exists
    reviewed_user = db.query(User).filter(User.id == review.reviewed_user_id).first()
    if not reviewed_user:
        raise HTTPException(
            status_code=404, detail="User not found. Cannot review a non-existent user."
        )

    # Prevent self-reviews
    if review.reviewed_user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot review yourself. You can only review other users.",
        )

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
        raise HTTPException(
            status_code=400,
            detail="You have already reviewed this user for this listing.",
        )
