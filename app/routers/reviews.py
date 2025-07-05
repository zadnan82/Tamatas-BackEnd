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


# Fix in app/routers/reviews.py - Replace the create_review function


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

        # Check for existing review
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
            print(f"Existing review ID: {existing_review.id}")
            print(f"Existing review anonymous: {existing_review.is_anonymous}")
            print(f"Existing review show_reviewer: {existing_review.show_reviewer}")
            raise HTTPException(status_code=400, detail=error_msg)

        print("Validation passed. Creating review...")

        # FIXED: Properly set show_reviewer field
        db_review = Review(
            id=generate_id(),
            reviewer_id=current_user.id,
            reviewed_user_id=review.reviewed_user_id,
            listing_id=review.listing_id,
            rating=review.rating,
            comment=review.comment,
            trade_type=review.trade_type,
            product_quality=review.product_quality,
            communication=review.communication,
            delivery=review.delivery,
            is_anonymous=review.is_anonymous,
            show_reviewer=not review.is_anonymous,  # FIXED: Set to opposite of is_anonymous
        )

        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        print(f"Review created successfully: {db_review.id}")
        print(f"Review anonymous: {db_review.is_anonymous}")
        print(f"Review show_reviewer: {db_review.show_reviewer}")
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
    """Get reviews for a user with proper filtering logic"""
    print(f"\n=== GET USER REVIEWS ===")
    print(f"Requested user_id: {user_id}")
    print(f"Current user_id: {current_user.id if current_user else 'None'}")
    print(f"Include anonymous: {include_anonymous}")

    # Allow viewing own anonymous reviews
    if current_user and current_user.id == user_id:
        include_anonymous = True
        print("User viewing own reviews - including anonymous")

    # Start with base query
    query = db.query(Review).filter(Review.reviewed_user_id == user_id)
    print(f"Base query for user_id: {user_id}")

    # Count total reviews for this user
    total_reviews = query.count()
    print(f"Total reviews found: {total_reviews}")

    # FIXED: Don't filter by show_reviewer for public display
    # The filtering should be:
    # 1. If user is viewing their own reviews: show all (including anonymous)
    # 2. If user is viewing someone else's reviews: show all non-anonymous reviews
    # 3. Anonymous reviews should be shown but with hidden reviewer info

    if not include_anonymous:
        # Only filter out reviews that are anonymous AND not being viewed by the owner
        # This means: show all non-anonymous reviews + anonymous reviews (but hide reviewer info)
        pass  # Don't filter here, handle in post-processing

    # Get all reviews with reviewer info
    reviews = query.options(joinedload(Review.reviewer)).all()

    print(f"Reviews after query: {len(reviews)}")

    # Debug: print each review
    for i, review in enumerate(reviews):
        print(
            f"Review {i + 1}: ID={review.id}, Rating={review.rating}, Anonymous={review.is_anonymous}, Show_reviewer={review.show_reviewer}"
        )
        if review.reviewer:
            print(f"  Reviewer: {review.reviewer.email}")
        else:
            print(f"  Reviewer: None")

    # Post-process: Hide reviewer info for anonymous reviews when viewed by others
    processed_reviews = []
    for review in reviews:
        if review.is_anonymous and not include_anonymous:
            # For anonymous reviews viewed by others: hide reviewer info but show the review
            review_copy = review  # Keep the review
            review_copy.reviewer = None  # Hide reviewer info
            processed_reviews.append(review_copy)
            print(f"Hidden reviewer for anonymous review: {review.id}")
        else:
            # For non-anonymous reviews or owner viewing their own: show normally
            processed_reviews.append(review)
            print(f"Showing review normally: {review.id}")

    print(f"Final processed reviews: {len(processed_reviews)}")
    print("=== END GET USER REVIEWS ===\n")

    return processed_reviews
