# app/routers/messages.py - Fixed with trailing slash handling
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

# IMPORTANT: Add include_in_schema=False to avoid redirect issues
router = APIRouter(prefix="/messages", tags=["messages"], include_in_schema=True)

print("✅ messages.py router loaded")


@router.post("/", response_model=MessageSchema)
@router.post(
    "", response_model=MessageSchema
)  # Handle both with and without trailing slash
def send_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Send a new message - REQUIRES AUTHENTICATION"""
    print(f"🔐 POST /messages called by user: {current_user.id} ({current_user.email})")
    print(
        f"🔐 Message data: recipient={message.recipient_id}, content='{message.content[:20]}...', listing={message.listing_id}"
    )

    # Verify recipient exists
    recipient = db.query(User).filter(User.id == message.recipient_id).first()
    if not recipient:
        print(f"❌ Recipient not found: {message.recipient_id}")
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Verify listing exists if provided
    listing = None
    if message.listing_id:
        listing = db.query(Listing).filter(Listing.id == message.listing_id).first()
        if not listing:
            print(f"❌ Listing not found: {message.listing_id}")
            raise HTTPException(status_code=404, detail="Listing not found")

    try:
        db_message = Message(
            id=generate_id(),
            sender_id=current_user.id,
            recipient_id=message.recipient_id,
            content=message.content,
            listing_id=message.listing_id,
            message_type=getattr(message, "message_type", "general"),
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        print(f"✅ Message created successfully: {db_message.id}")

        # Send notification email
        if listing:
            try:
                send_new_message_notification.delay(
                    recipient.email,
                    current_user.full_name or current_user.email,
                    listing.title,
                )
                print("✅ Notification email queued")
            except Exception as e:
                print(f"⚠️ Failed to queue notification email: {e}")

        return db_message

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/", response_model=List[MessageSchema])
@router.get(
    "", response_model=List[MessageSchema]
)  # Handle both with and without trailing slash
def get_messages(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get all messages for current user - REQUIRES AUTHENTICATION"""
    print(f"🔐 GET /messages called by user: {current_user.id} ({current_user.email})")

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
    print(f"Found {len(messages)} messages")
    return messages


@router.get("/conversations/{user_id}", response_model=List[MessageSchema])
def get_conversation(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get conversation with a specific user - REQUIRES AUTHENTICATION"""
    print(f"🔐 GET /messages/conversations/{user_id} called by user: {current_user.id}")

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
    print(f"Found {len(messages)} messages in conversation")
    return messages


@router.put("/{message_id}/read")
def mark_message_read(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Mark a message as read - REQUIRES AUTHENTICATION"""
    print(f"🔐 PUT /messages/{message_id}/read called by user: {current_user.id}")

    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.recipient_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to mark this message as read"
        )

    message.read = True
    db.commit()
    print(f"✅ Message {message_id} marked as read")
    return {"message": "Message marked as read"}
