# app/models.py - COMPLETE FILE - Fresh Trade v2.0 with Location & Contact Features

from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Enum,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# ==================== ENUMS ====================


class ListingType(str, enum.Enum):
    for_sale = "for_sale"
    looking_for = "looking_for"
    give_away = "give_away"  # NEW: Free produce sharing


class ListingStatus(str, enum.Enum):
    active = "active"
    pending = "pending"
    completed = "completed"
    expired = "expired"


class TradePreference(str, enum.Enum):
    sale_only = "sale_only"
    trade_only = "trade_only"
    both = "both"


class PriceUnit(str, enum.Enum):
    per_lb = "per_lb"
    per_kg = "per_kg"
    per_piece = "per_piece"
    per_dozen = "per_dozen"
    per_bag = "per_bag"


class MessageType(str, enum.Enum):
    inquiry = "inquiry"
    offer = "offer"
    general = "general"


class TradeType(str, enum.Enum):
    sale = "sale"
    trade = "trade"
    purchase = "purchase"


class ForumCategory(str, enum.Enum):
    gardening_tips = "gardening_tips"
    trading_ideas = "trading_ideas"
    general_discussion = "general_discussion"
    site_feedback = "site_feedback"


# NEW: Contact preference enum
class ContactPreference(str, enum.Enum):
    messages_only = "messages_only"
    whatsapp_only = "whatsapp_only"
    both = "both"


# ==================== MODELS ====================


class User(Base):
    __tablename__ = "users"

    # Basic user fields
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())

    # NEW: Location fields - MANDATORY for creating listings
    location = Column(
        JSON, nullable=True
    )  # {country, city, state, area, formatted_address}
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_precision = Column(String, default="city")  # "city" or "neighborhood"
    search_radius = Column(Integer, default=25)  # Default search radius in miles

    # NEW: Contact preference fields
    whatsapp_number = Column(String, nullable=True)
    contact_preference = Column(Enum(ContactPreference), default=ContactPreference.both)
    show_whatsapp_on_listings = Column(Boolean, default=False)

    # Relationships
    listings = relationship("Listing", back_populates="owner")
    sent_messages = relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender"
    )
    received_messages = relationship(
        "Message", foreign_keys="Message.recipient_id", back_populates="recipient"
    )
    reviews_given = relationship(
        "Review", foreign_keys="Review.reviewer_id", back_populates="reviewer"
    )
    reviews_received = relationship(
        "Review", foreign_keys="Review.reviewed_user_id", back_populates="reviewed_user"
    )
    favorites = relationship("Favorite", back_populates="user")
    forum_topics = relationship("ForumTopic", back_populates="creator")
    forum_posts = relationship("ForumPost", back_populates="author")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=True)
    listing_type = Column(Enum(ListingType), nullable=False)  # Updated with give_away
    price = Column(Float, nullable=True)  # NOW OPTIONAL for give_away listings
    price_unit = Column(Enum(PriceUnit), default=PriceUnit.per_lb)
    quantity_available = Column(String, nullable=True)
    trade_preference = Column(Enum(TradePreference), default=TradePreference.both)
    images = Column(JSON, nullable=True)  # Array of image URLs
    status = Column(Enum(ListingStatus), default=ListingStatus.active)
    harvest_date = Column(DateTime, nullable=True)
    organic = Column(Boolean, default=False)
    location = Column(
        JSON, nullable=False
    )  # MANDATORY - {city, state, latitude, longitude}
    view_count = Column(Integer, default=0)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="listings")
    messages = relationship("Message", back_populates="listing")
    reviews = relationship("Review", back_populates="listing")
    favorites = relationship("Favorite", back_populates="listing")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(String, ForeignKey("users.id"), nullable=False)
    listing_id = Column(String, ForeignKey("listings.id"), nullable=True)
    content = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    message_type = Column(Enum(MessageType), default=MessageType.general)
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sender = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_messages"
    )
    recipient = relationship(
        "User", foreign_keys=[recipient_id], back_populates="received_messages"
    )
    listing = relationship("Listing", back_populates="messages")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, index=True)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=False)
    reviewed_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    listing_id = Column(String, ForeignKey("listings.id"), nullable=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    trade_type = Column(Enum(TradeType), nullable=True)
    product_quality = Column(Integer, nullable=True)  # 1-5
    communication = Column(Integer, nullable=True)  # 1-5
    delivery = Column(Integer, nullable=True)  # 1-5
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    reviewer = relationship(
        "User", foreign_keys=[reviewer_id], back_populates="reviews_given"
    )
    reviewed_user = relationship(
        "User", foreign_keys=[reviewed_user_id], back_populates="reviews_received"
    )
    listing = relationship("Listing", back_populates="reviews")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    listing_id = Column(String, ForeignKey("listings.id"), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="favorites")
    listing = relationship("Listing", back_populates="favorites")


class ForumTopic(Base):
    __tablename__ = "forum_topics"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(Enum(ForumCategory), nullable=False)
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="forum_topics")
    posts = relationship("ForumPost", back_populates="topic")


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id = Column(String, primary_key=True, index=True)
    topic_id = Column(String, ForeignKey("forum_topics.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_post_id = Column(String, ForeignKey("forum_posts.id"), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    topic = relationship("ForumTopic", back_populates="posts")
    author = relationship("User", back_populates="forum_posts")
    replies = relationship("ForumPost", remote_side=[id])


class ForumTopicLike(Base):
    __tablename__ = "forum_topic_likes"

    id = Column(String, primary_key=True, index=True)
    topic_id = Column(String, ForeignKey("forum_topics.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    topic = relationship("ForumTopic")
    user = relationship("User")

    # Ensure one like per user per topic
    __table_args__ = (Index("ix_topic_user_like", "topic_id", "user_id", unique=True),)


class ForumPostLike(Base):
    __tablename__ = "forum_post_likes"

    id = Column(String, primary_key=True, index=True)
    post_id = Column(String, ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    post = relationship("ForumPost")
    user = relationship("User")

    # Ensure one like per user per post
    __table_args__ = (Index("ix_post_user_like", "post_id", "user_id", unique=True),)
