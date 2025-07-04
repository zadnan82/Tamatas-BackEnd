# UPDATE app/schemas.py - Complete updated schemas

from pydantic import BaseModel, EmailStr, validator
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
    ContactPreference,  # NEW
)


# User Schemas - UPDATED with location and contact fields
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_image: Optional[str] = None


class UserCreate(UserBase):
    password: str
    # MANDATORY LOCATION FIELDS for new users
    location: Dict[str, Any]  # {country, city, state, area}
    location_precision: Optional[str] = "city"  # "city" or "neighborhood"
    search_radius: Optional[int] = 25

    # OPTIONAL CONTACT FIELDS
    whatsapp_number: Optional[str] = None
    contact_preference: Optional[ContactPreference] = ContactPreference.both
    show_whatsapp_on_listings: Optional[bool] = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    profile_image: Optional[str] = None

    # LOCATION UPDATES
    location: Optional[Dict[str, Any]] = None
    location_precision: Optional[str] = None
    search_radius: Optional[int] = None

    # CONTACT UPDATES
    whatsapp_number: Optional[str] = None
    contact_preference: Optional[ContactPreference] = None
    show_whatsapp_on_listings: Optional[bool] = None


# NEW: Location-specific schemas
class LocationUpdate(BaseModel):
    address: str
    location_precision: Optional[str] = "city"
    search_radius: Optional[int] = 25


class LocationSuggestion(BaseModel):
    display_name: str
    city: str
    state: Optional[str] = None
    country: str
    latitude: float
    longitude: float
    type: str


class User(UserBase):
    id: str
    is_active: bool
    created_date: datetime
    updated_date: Optional[datetime] = None

    # LOCATION FIELDS
    location: Optional[Dict[str, Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_precision: Optional[str] = None
    search_radius: Optional[int] = None

    # CONTACT FIELDS
    whatsapp_number: Optional[str] = None
    contact_preference: Optional[ContactPreference] = None
    show_whatsapp_on_listings: Optional[bool] = None

    class Config:
        from_attributes = True


class UserProfile(User):
    average_rating: Optional[float] = None
    total_reviews: int = 0
    total_listings: int = 0


# Listing Schemas - UPDATED with mandatory location and optional price
class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    listing_type: ListingType
    price: Optional[float] = None  # Optional for give_away listings
    price_unit: Optional[PriceUnit] = PriceUnit.per_lb
    quantity_available: Optional[str] = None
    trade_preference: Optional[TradePreference] = TradePreference.both
    images: Optional[List[str]] = None
    harvest_date: Optional[datetime] = None
    organic: Optional[bool] = False
    location: Dict[str, Any]  # MANDATORY - must include lat/lng

    @validator("price")
    def validate_price_for_listing_type(cls, v, values):
        """Price is required for for_sale, optional for give_away"""
        listing_type = values.get("listing_type")
        if listing_type == ListingType.for_sale and v is None:
            raise ValueError("Price is required for sale listings")
        if listing_type == ListingType.give_away and v is not None:
            # Allow price to be set to 0 for give_away, but warn user
            pass
        return v


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


# NEW: Listing with distance information
class ListingWithDistance(BaseModel):
    listing: Listing
    distance: Optional[float] = None  # Distance in miles
    distance_km: Optional[float] = None  # Distance in kilometers


# Message Schemas (unchanged)
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


# Review Schemas (unchanged)
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


# Favorite Schemas (unchanged)
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


# Forum Schemas (unchanged)
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
    like_count: Optional[int] = 0
    user_liked: Optional[bool] = False

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
    like_count: Optional[int] = 0
    user_liked: Optional[bool] = False

    class Config:
        from_attributes = True


# Auth Schemas (unchanged)
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# File Upload Schema (unchanged)
class FileUpload(BaseModel):
    file_url: str
    filename: str


# Contact Form Schema (unchanged)
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


# NEW: Search and filter schemas
class LocationSearchParams(BaseModel):
    latitude: float
    longitude: float
    radius: Optional[int] = 25
    category: Optional[str] = None
    listing_type: Optional[ListingType] = None
    organic_only: Optional[bool] = False


class SearchFilters(BaseModel):
    search: Optional[str] = None
    category: Optional[str] = None
    listing_type: Optional[str] = None
    location: Optional[str] = None
    organic_only: Optional[bool] = False
    near_me: Optional[bool] = False
    radius: Optional[int] = 25
    sort_by: Optional[str] = "created_date"
    sort_order: Optional[str] = "desc"


# NEW: Map-related schemas
class MapBounds(BaseModel):
    sw_lat: float
    sw_lng: float
    ne_lat: float
    ne_lng: float


class MapListing(BaseModel):
    id: str
    title: str
    category: str
    listing_type: ListingType
    price: Optional[float] = None
    latitude: float
    longitude: float
    images: Optional[List[str]] = None
    owner_name: Optional[str] = None


# NEW: Contact information for listings
class ContactInfo(BaseModel):
    can_message: bool = True
    can_whatsapp: bool = False
    whatsapp_url: Optional[str] = None
    contact_preference: ContactPreference
