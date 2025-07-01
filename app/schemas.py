from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import (
    ListingType,
    ListingStatus,
    TradePreference,
    PriceUnit,
    MessageType,
    TradeType,
    ForumCategory,
)


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_image: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_image: Optional[str] = None


class User(UserBase):
    id: str
    is_active: bool
    created_date: datetime
    updated_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfile(User):
    average_rating: Optional[float] = None
    total_reviews: int = 0
    total_listings: int = 0


# Listing Schemas
class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    listing_type: ListingType
    price: Optional[float] = None
    price_unit: Optional[PriceUnit] = PriceUnit.per_lb
    quantity_available: Optional[str] = None
    trade_preference: Optional[TradePreference] = TradePreference.both
    images: Optional[List[str]] = None
    harvest_date: Optional[datetime] = None
    organic: Optional[bool] = False
    location: Optional[Dict[str, Any]] = None


class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    price_unit: Optional[PriceUnit] = None
    quantity_available: Optional[str] = None
    trade_preference: Optional[TradePreference] = None
    images: Optional[List[str]] = None
    harvest_date: Optional[datetime] = None
    organic: Optional[bool] = None
    location: Optional[Dict[str, Any]] = None


class Listing(ListingBase):
    id: str
    status: ListingStatus
    view_count: int
    created_by: str
    created_date: datetime
    updated_date: Optional[datetime] = None
    owner: User

    class Config:
        from_attributes = True


# Message Schemas
class MessageBase(BaseModel):
    recipient_id: str
    listing_id: Optional[str] = None
    content: str
    message_type: Optional[MessageType] = MessageType.general


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: str
    sender_id: str
    read: bool
    created_date: datetime
    sender: User
    recipient: User
    listing: Optional[Listing] = None

    class Config:
        from_attributes = True


# Review Schemas
class ReviewBase(BaseModel):
    reviewed_user_id: str
    listing_id: Optional[str] = None
    rating: int
    comment: Optional[str] = None
    trade_type: Optional[TradeType] = None
    product_quality: Optional[int] = None
    communication: Optional[int] = None
    delivery: Optional[int] = None


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    id: str
    reviewer_id: str
    created_date: datetime
    reviewer: User
    reviewed_user: User

    class Config:
        from_attributes = True


# Favorite Schemas
class FavoriteCreate(BaseModel):
    listing_id: str


class Favorite(BaseModel):
    id: str
    user_id: str
    listing_id: str
    created_date: datetime
    listing: Listing

    class Config:
        from_attributes = True


# Forum Schemas
class ForumTopicBase(BaseModel):
    title: str
    content: str
    category: ForumCategory


class ForumTopicCreate(ForumTopicBase):
    pass


class ForumTopic(ForumTopicBase):
    id: str
    is_pinned: bool
    is_locked: bool
    view_count: int
    created_by: str
    created_date: datetime
    creator: User
    post_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ForumPostBase(BaseModel):
    topic_id: str
    content: str
    parent_post_id: Optional[str] = None


class ForumPostCreate(ForumPostBase):
    pass


class ForumPost(ForumPostBase):
    id: str
    created_by: str
    created_date: datetime
    author: User

    class Config:
        from_attributes = True


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# File Upload Schema
class FileUpload(BaseModel):
    file_url: str
    filename: str


# Contact Form Schema
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
