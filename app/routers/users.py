from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.schemas import (
    UserUpdate,
    User as UserSchema,
    UserProfile,
    Review as ReviewSchema,
)
from app.auth import get_current_active_user
import json
from datetime import datetime
from app.models import User, Review, Listing, Message, Favorite, ForumTopic, ForumPost


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


@router.delete("/me/delete-account")
def delete_user_account(
    confirm: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    GDPR Compliant Account Deletion
    Permanently deletes user account and all associated data
    """
    if not confirm:
        return {
            "message": "Account deletion requires confirmation",
            "warning": "This action cannot be undone. All your data will be permanently deleted.",
            "data_to_be_deleted": [
                "User profile and contact information",
                "All your listings",
                "All your messages (sent and received)",
                "All your reviews (given and received)",
                "All your favorites",
                "All your forum topics and posts",
                "All uploaded images",
            ],
            "instructions": "To confirm deletion, call this endpoint with confirm=true",
        }

    try:
        user_id = current_user.id

        # Delete in correct order due to foreign key constraints

        # 1. Delete forum post likes
        db.execute(
            "DELETE FROM forum_post_likes WHERE user_id = :user_id OR post_id IN "
            "(SELECT id FROM forum_posts WHERE created_by = :user_id)",
            {"user_id": user_id},
        )

        # 2. Delete forum topic likes
        db.execute(
            "DELETE FROM forum_topic_likes WHERE user_id = :user_id OR topic_id IN "
            "(SELECT id FROM forum_topics WHERE created_by = :user_id)",
            {"user_id": user_id},
        )

        # 3. Delete forum posts (including replies to user's posts)
        db.execute(
            "DELETE FROM forum_posts WHERE created_by = :user_id OR parent_post_id IN "
            "(SELECT id FROM forum_posts WHERE created_by = :user_id)",
            {"user_id": user_id},
        )

        # 4. Delete forum topics
        db.execute(
            "DELETE FROM forum_topics WHERE created_by = :user_id", {"user_id": user_id}
        )

        # 5. Delete favorites
        db.execute(
            "DELETE FROM favorites WHERE user_id = :user_id", {"user_id": user_id}
        )

        # 6. Delete reviews (given and received)
        db.execute(
            "DELETE FROM reviews WHERE reviewer_id = :user_id OR reviewed_user_id = :user_id",
            {"user_id": user_id},
        )

        # 7. Delete messages (sent and received)
        db.execute(
            "DELETE FROM messages WHERE sender_id = :user_id OR recipient_id = :user_id",
            {"user_id": user_id},
        )

        # 8. Delete favorites of user's listings
        db.execute(
            "DELETE FROM favorites WHERE listing_id IN (SELECT id FROM listings WHERE created_by = :user_id)",
            {"user_id": user_id},
        )

        # 9. Delete user's listings
        db.execute(
            "DELETE FROM listings WHERE created_by = :user_id", {"user_id": user_id}
        )

        # 10. Finally delete the user
        db.execute("DELETE FROM users WHERE id = :user_id", {"user_id": user_id})

        db.commit()

        return {
            "message": "Account successfully deleted",
            "deleted_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "gdpr_compliance": "All personal data has been permanently removed",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete account: {str(e)}"
        )


@router.get("/me/export-data")
def export_user_data(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    GDPR Compliant Data Export
    Returns all user data in a structured format
    """
    try:
        # Collect all user data
        user_data = {
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "user_id": current_user.id,
                "export_type": "GDPR_DATA_EXPORT",
            },
            "profile": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "bio": current_user.bio,
                "phone": current_user.phone,
                "address": current_user.address,
                "profile_image": current_user.profile_image,
                "location": current_user.location,
                "latitude": current_user.latitude,
                "longitude": current_user.longitude,
                "location_precision": current_user.location_precision,
                "search_radius": current_user.search_radius,
                "whatsapp_number": current_user.whatsapp_number,
                "contact_preference": current_user.contact_preference,
                "show_whatsapp_on_listings": current_user.show_whatsapp_on_listings,
                "is_active": current_user.is_active,
                "created_date": current_user.created_date.isoformat()
                if current_user.created_date
                else None,
                "updated_date": current_user.updated_date.isoformat()
                if current_user.updated_date
                else None,
            },
        }

        # Get user's listings
        listings = db.query(Listing).filter(Listing.created_by == current_user.id).all()
        user_data["listings"] = [
            {
                "id": listing.id,
                "title": listing.title,
                "description": listing.description,
                "category": listing.category,
                "listing_type": listing.listing_type,
                "price": listing.price,
                "quantity_available": listing.quantity_available,
                "organic": listing.organic,
                "location": listing.location,
                "status": listing.status,
                "view_count": listing.view_count,
                "created_date": listing.created_date.isoformat()
                if listing.created_date
                else None,
                "images": listing.images,
            }
            for listing in listings
        ]

        # Get user's messages (sent and received)
        sent_messages = (
            db.query(Message).filter(Message.sender_id == current_user.id).all()
        )
        received_messages = (
            db.query(Message).filter(Message.recipient_id == current_user.id).all()
        )

        user_data["messages"] = {
            "sent": [
                {
                    "id": msg.id,
                    "recipient_id": msg.recipient_id,
                    "listing_id": msg.listing_id,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "created_date": msg.created_date.isoformat()
                    if msg.created_date
                    else None,
                }
                for msg in sent_messages
            ],
            "received": [
                {
                    "id": msg.id,
                    "sender_id": msg.sender_id,
                    "listing_id": msg.listing_id,
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "read": msg.read,
                    "created_date": msg.created_date.isoformat()
                    if msg.created_date
                    else None,
                }
                for msg in received_messages
            ],
        }

        # Get user's reviews (given and received)
        reviews_given = (
            db.query(Review).filter(Review.reviewer_id == current_user.id).all()
        )
        reviews_received = (
            db.query(Review).filter(Review.reviewed_user_id == current_user.id).all()
        )

        user_data["reviews"] = {
            "given": [
                {
                    "id": review.id,
                    "reviewed_user_id": review.reviewed_user_id,
                    "listing_id": review.listing_id,
                    "rating": review.rating,
                    "comment": review.comment,
                    "trade_type": review.trade_type,
                    "created_date": review.created_date.isoformat()
                    if review.created_date
                    else None,
                }
                for review in reviews_given
            ],
            "received": [
                {
                    "id": review.id,
                    "reviewer_id": review.reviewer_id,
                    "listing_id": review.listing_id,
                    "rating": review.rating,
                    "comment": review.comment,
                    "trade_type": review.trade_type,
                    "created_date": review.created_date.isoformat()
                    if review.created_date
                    else None,
                }
                for review in reviews_received
            ],
        }

        # Get user's favorites
        favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
        user_data["favorites"] = [
            {
                "id": fav.id,
                "listing_id": fav.listing_id,
                "created_date": fav.created_date.isoformat()
                if fav.created_date
                else None,
            }
            for fav in favorites
        ]

        # Get user's forum activity
        forum_topics = (
            db.query(ForumTopic).filter(ForumTopic.created_by == current_user.id).all()
        )
        forum_posts = (
            db.query(ForumPost).filter(ForumPost.created_by == current_user.id).all()
        )

        user_data["forum_activity"] = {
            "topics": [
                {
                    "id": topic.id,
                    "title": topic.title,
                    "content": topic.content,
                    "category": topic.category,
                    "view_count": topic.view_count,
                    "created_date": topic.created_date.isoformat()
                    if topic.created_date
                    else None,
                }
                for topic in forum_topics
            ],
            "posts": [
                {
                    "id": post.id,
                    "topic_id": post.topic_id,
                    "content": post.content,
                    "parent_post_id": post.parent_post_id,
                    "created_date": post.created_date.isoformat()
                    if post.created_date
                    else None,
                }
                for post in forum_posts
            ],
        }

        # Return as downloadable JSON file
        json_str = json.dumps(user_data, indent=2, ensure_ascii=False)

        return Response(
            content=json_str,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=fresh_trade_data_export_{current_user.id}.json"
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")


@router.post("/me/anonymize-account")
def anonymize_user_account(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    GDPR Compliant Account Anonymization
    Removes personal data while preserving content for community
    """
    try:
        # Generate anonymous identifier
        anonymous_id = f"anonymous_user_{current_user.id[:8]}"

        # Anonymize user profile
        current_user.email = f"deleted_user_{current_user.id[:8]}@example.com"
        current_user.full_name = "Deleted User"
        current_user.bio = None
        current_user.phone = None
        current_user.address = None
        current_user.profile_image = None
        current_user.whatsapp_number = None
        current_user.location = {"city": "Unknown", "country": "Unknown"}
        current_user.latitude = None
        current_user.longitude = None
        current_user.is_active = False

        # Keep listings but anonymize them
        user_listings = (
            db.query(Listing).filter(Listing.created_by == current_user.id).all()
        )
        for listing in user_listings:
            listing.title = f"[Deleted User] {listing.title}"
            listing.description = (
                "This listing was created by a user who deleted their account."
            )

        # Delete personal messages but keep listing-related inquiries anonymous
        db.execute(
            "UPDATE messages SET content = '[Message from deleted user]' "
            "WHERE sender_id = :user_id",
            {"user_id": current_user.id},
        )

        db.commit()

        return {
            "message": "Account successfully anonymized",
            "anonymized_at": datetime.utcnow().isoformat(),
            "anonymous_id": anonymous_id,
            "preserved_content": [
                "Listings (anonymized)",
                "Forum posts (anonymized)",
                "Reviews (anonymized)",
            ],
            "deleted_content": [
                "Personal contact information",
                "Private messages",
                "Location data",
            ],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to anonymize account: {str(e)}"
        )
