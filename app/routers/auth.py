# app/routers/auth.py - FIXED VERSION with no duplicates

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, User as UserSchema, Token
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
)
from app.utils import generate_id
from app.config import settings
from app.location_utils import LocationService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register new user with mandatory location and return access token"""

    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate location data
    if not user.location:
        raise HTTPException(
            status_code=400,
            detail="Location is required. Please provide at least country and city.",
        )

    # Validate required location fields
    required_fields = ["country", "city"]
    missing_fields = [
        field for field in required_fields if not user.location.get(field)
    ]
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required location fields: {', '.join(missing_fields)}",
        )

    # Geocode the location if coordinates not provided
    location_data = user.location.copy()
    if not location_data.get("latitude") or not location_data.get("longitude"):
        # Build address string for geocoding
        address_parts = []
        if location_data.get("area"):
            address_parts.append(location_data["area"])
        if location_data.get("city"):
            address_parts.append(location_data["city"])
        if location_data.get("state"):
            address_parts.append(location_data["state"])
        if location_data.get("country"):
            address_parts.append(location_data["country"])

        address = ", ".join(address_parts)

        try:
            geocoded = await LocationService.geocode_address(address)
            if geocoded:
                location_data.update(
                    {
                        "latitude": geocoded["latitude"],
                        "longitude": geocoded["longitude"],
                        "formatted_address": geocoded.get("formatted_address", address),
                    }
                )
                # Fill in any missing details from geocoding
                if not location_data.get("state") and geocoded.get("state"):
                    location_data["state"] = geocoded["state"]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Could not verify location. Please check your address and try again.",
                )
        except Exception as e:
            raise HTTPException(
                status_code=400, detail="Failed to process location. Please try again."
            )

    # Validate WhatsApp number if provided
    if user.whatsapp_number:
        from app.location_utils import ContactService

        if not ContactService.validate_phone_number(user.whatsapp_number):
            raise HTTPException(
                status_code=400, detail="Invalid WhatsApp number format"
            )

    try:
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            id=generate_id(),
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            bio=user.bio,
            phone=user.phone,
            address=user.address,
            profile_image=user.profile_image,
            # LOCATION FIELDS - MANDATORY
            location=location_data,
            latitude=location_data.get("latitude"),
            longitude=location_data.get("longitude"),
            location_precision=user.location_precision or "city",
            search_radius=user.search_radius or 25,
            # CONTACT FIELDS - OPTIONAL
            whatsapp_number=user.whatsapp_number,
            contact_preference=user.contact_preference,
            show_whatsapp_on_listings=user.show_whatsapp_on_listings or False,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # ✅ Create access token and return it (like login does)
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": db_user.email}, expires_delta=access_token_expires
        )

        print(
            f"✅ User registered with location: {db_user.email} in {location_data.get('city')}, {location_data.get('country')}"
        )

        # Return token response (same format as login)
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        db.rollback()
        print(f"❌ Registration failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Login user - unchanged functionality"""
    # OAuth2PasswordRequestForm uses 'username' field, but we'll treat it as email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    print(f"✅ User logged in: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user


@router.post("/validate-location")
async def validate_location(location_data: dict):
    """Validate location data during registration"""
    try:
        # Check required fields
        required_fields = ["country", "city"]
        missing_fields = [
            field for field in required_fields if not location_data.get(field)
        ]
        if missing_fields:
            return {
                "valid": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
            }

        # Try to geocode
        address_parts = []
        if location_data.get("area"):
            address_parts.append(location_data["area"])
        if location_data.get("city"):
            address_parts.append(location_data["city"])
        if location_data.get("state"):
            address_parts.append(location_data["state"])
        if location_data.get("country"):
            address_parts.append(location_data["country"])

        address = ", ".join(address_parts)
        geocoded = await LocationService.geocode_address(address)

        if geocoded:
            return {
                "valid": True,
                "geocoded": geocoded,
                "formatted_address": geocoded.get("formatted_address"),
            }
        else:
            return {
                "valid": False,
                "error": "Could not find this location. Please check your spelling.",
            }

    except Exception as e:
        return {
            "valid": False,
            "error": "Failed to validate location. Please try again.",
        }


print(f"✅ Auth router configured with location validation and token response")
