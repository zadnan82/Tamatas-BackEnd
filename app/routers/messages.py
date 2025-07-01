from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.database import get_db
from app.models import User, Message, Listing
from app.schemas import MessageCreate, Message as MessageSchema
from app.auth import get_current_active_user
from app.utils import generate_id
from app.tasks import send_new_message_notification

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageSchema)
def send_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Verify recipient exists
    recipient = db.query(User).filter(User.id == message.recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Verify listing exists if provided
    listing = None
    if message.listing_id:
        listing = db.query(Listing).filter(Listing.id == message.listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

    db_message = Message(id=generate_id(), sender_id=current_user.id, **message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Send notification email
    if listing:
        send_new_message_notification.delay(
            recipient.email, current_user.full_name or current_user.email, listing.title
        )

    return db_message


@router.get("/", response_model=List[MessageSchema])
def get_messages(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    messages = (
        db.query(Message)
        .filter(
            or_(
                Message.sender_id == current_user.id,
                Message.recipient_id == current_user.id,
            )
        )
        .order_by(Message.created_date.desc())
        .all()
    )
    return messages


@router.get("/conversations/{user_id}", response_model=List[MessageSchema])
def get_conversation(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(Message)
        .filter(
            or_(
                and_(
                    Message.sender_id == current_user.id,
                    Message.recipient_id == user_id,
                ),
                and_(
                    Message.sender_id == user_id,
                    Message.recipient_id == current_user.id,
                ),
            )
        )
        .order_by(Message.created_date.asc())
        .all()
    )
    return messages


@router.put("/{message_id}/read")
def mark_message_read(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.recipient_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to mark this message as read"
        )

    message.read = True
    db.commit()
    return {"message": "Message marked as read"}


# ===================================
# File: app/routers/reviews.py

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
