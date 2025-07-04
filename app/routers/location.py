# CREATE NEW FILE: app/routers/location.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, Listing
from app.schemas import (
    LocationUpdate,
    LocationSuggestion,
    ListingWithDistance,
    MapListing,
    ContactInfo,
)
from app.auth import get_current_active_user
from app.location_utils import LocationService, ContactService

router = APIRouter(prefix="/location", tags=["location"])


@router.put("/update-user-location")
async def update_user_location(
    location_data: LocationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user's location based on address"""
    try:
        geocoded = await LocationService.geocode_address(location_data.address)
        if not geocoded:
            raise HTTPException(
                status_code=400,
                detail="Could not find location. Please try a different address.",
            )

        # Update user location
        current_user.latitude = geocoded["latitude"]
        current_user.longitude = geocoded["longitude"]
        current_user.location = {
            "country": geocoded["country"],
            "city": geocoded["city"],
            "state": geocoded["state"],
            "area": geocoded.get("area"),
            "formatted_address": geocoded["formatted_address"],
        }
        current_user.location_precision = location_data.location_precision
        current_user.search_radius = location_data.search_radius

        db.commit()
        db.refresh(current_user)

        return {
            "message": "Location updated successfully",
            "location": current_user.location,
            "coordinates": {
                "latitude": current_user.latitude,
                "longitude": current_user.longitude,
            },
            "search_radius": current_user.search_radius,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update location: {str(e)}"
        )


@router.get("/search-locations", response_model=List[LocationSuggestion])
async def search_locations(
    q: str = Query(..., min_length=2, description="Search query for location"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of suggestions"),
):
    """Get location suggestions for autocomplete"""
    try:
        suggestions = await LocationService.search_locations(q, limit)
        return [LocationSuggestion(**suggestion) for suggestion in suggestions]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search locations: {str(e)}"
        )


@router.get("/nearby-listings")
def get_nearby_listings(
    radius: Optional[int] = Query(None, description="Search radius in miles"),
    category: Optional[str] = Query(None, description="Filter by category"),
    listing_type: Optional[str] = Query(None, description="Filter by listing type"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get listings within user's radius with distance information"""
    if not current_user.latitude or not current_user.longitude:
        raise HTTPException(
            status_code=400,
            detail="User location not set. Please update your location first.",
        )

    search_radius = radius or current_user.search_radius or 25

    # Build query
    query = db.query(Listing).filter(
        Listing.status == "active", Listing.location.isnot(None)
    )

    if category and category != "all":
        query = query.filter(Listing.category == category)

    if listing_type and listing_type != "all":
        query = query.filter(Listing.listing_type == listing_type)

    listings = query.all()

    # Filter by distance and add distance info
    nearby_listings = []
    for listing in listings:
        if (
            listing.location
            and listing.location.get("latitude")
            and listing.location.get("longitude")
        ):
            distance = LocationService.calculate_distance(
                current_user.latitude,
                current_user.longitude,
                float(listing.location["latitude"]),
                float(listing.location["longitude"]),
            )

            if distance <= search_radius:
                distance_km = LocationService.calculate_distance_km(
                    current_user.latitude,
                    current_user.longitude,
                    float(listing.location["latitude"]),
                    float(listing.location["longitude"]),
                )

                listing_with_distance = ListingWithDistance(
                    listing=listing,
                    distance=round(distance, 1),
                    distance_km=round(distance_km, 1),
                )
                nearby_listings.append(listing_with_distance)

    # Sort by distance
    nearby_listings.sort(key=lambda x: x.distance)

    return nearby_listings[:limit]


@router.get("/listings-for-map", response_model=List[MapListing])
def get_listings_for_map(
    bounds: str = Query(..., description="Map bounds: sw_lat,sw_lng,ne_lat,ne_lng"),
    category: Optional[str] = Query(None, description="Filter by category"),
    listing_type: Optional[str] = Query(None, description="Filter by listing type"),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get listings within map bounds for map display"""
    try:
        sw_lat, sw_lng, ne_lat, ne_lng = map(float, bounds.split(","))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid bounds format. Use: sw_lat,sw_lng,ne_lat,ne_lng",
        )

    # Build query
    query = db.query(Listing).filter(
        Listing.status == "active", Listing.location.isnot(None)
    )

    if category and category != "all":
        query = query.filter(Listing.category == category)

    if listing_type and listing_type != "all":
        query = query.filter(Listing.listing_type == listing_type)

    listings = query.limit(limit * 2).all()  # Get more to filter

    # Filter listings within bounds
    map_listings = []
    for listing in listings:
        if (
            listing.location
            and listing.location.get("latitude")
            and listing.location.get("longitude")
        ):
            lat = float(listing.location["latitude"])
            lng = float(listing.location["longitude"])

            # Check if within bounds
            if sw_lat <= lat <= ne_lat and sw_lng <= lng <= ne_lng:
                map_listing = MapListing(
                    id=listing.id,
                    title=listing.title,
                    category=listing.category,
                    listing_type=listing.listing_type,
                    price=listing.price,
                    latitude=lat,
                    longitude=lng,
                    images=listing.images[:1] if listing.images else [],
                    owner_name=listing.owner.full_name
                    if listing.owner
                    else "Anonymous",
                )
                map_listings.append(map_listing)

                if len(map_listings) >= limit:
                    break

    return map_listings


@router.get("/search/location")
def search_listings_by_location(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius: int = Query(25, description="Search radius in miles"),
    category: Optional[str] = Query(None, description="Filter by category"),
    listing_type: Optional[str] = Query(None, description="Filter by listing type"),
    organic_only: bool = Query(False, description="Show only organic listings"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search listings by geographic location and radius"""

    # Validate coordinates
    if not LocationService.validate_coordinates(lat, lng):
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    # Build query
    query = db.query(Listing).filter(
        Listing.status == "active", Listing.location.isnot(None)
    )

    if category and category != "all":
        query = query.filter(Listing.category == category)

    if listing_type and listing_type != "all":
        query = query.filter(Listing.listing_type == listing_type)

    if organic_only:
        query = query.filter(Listing.organic == True)

    listings = query.all()

    # Filter by distance
    nearby_listings = []
    for listing in listings:
        if (
            listing.location
            and listing.location.get("latitude")
            and listing.location.get("longitude")
        ):
            distance = LocationService.calculate_distance(
                lat,
                lng,
                float(listing.location["latitude"]),
                float(listing.location["longitude"]),
            )

            if distance <= radius:
                # Add distance info to listing
                listing.distance = round(distance, 1)
                nearby_listings.append(listing)

    # Sort by distance
    nearby_listings.sort(key=lambda x: x.distance)

    return nearby_listings[:limit]


@router.get("/user-location")
def get_user_location(current_user: User = Depends(get_current_active_user)):
    """Get current user's location information"""
    return {
        "location": current_user.location,
        "coordinates": {
            "latitude": current_user.latitude,
            "longitude": current_user.longitude,
        }
        if current_user.latitude and current_user.longitude
        else None,
        "location_precision": current_user.location_precision,
        "search_radius": current_user.search_radius,
        "has_location": bool(current_user.latitude and current_user.longitude),
    }


@router.get("/contact-info/{listing_id}", response_model=ContactInfo)
def get_listing_contact_info(
    listing_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get contact information for a specific listing"""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    owner = listing.owner
    contact_info = ContactInfo(
        can_message=True,  # Always available through platform
        can_whatsapp=bool(owner.whatsapp_number and owner.show_whatsapp_on_listings),
        contact_preference=owner.contact_preference or "both",
    )

    # Generate WhatsApp URL if available
    if contact_info.can_whatsapp:
        message = ContactService.generate_whatsapp_message(
            listing.title, current_user.full_name or "Someone"
        )
        contact_info.whatsapp_url = ContactService.format_whatsapp_url(
            owner.whatsapp_number, message
        )

    return contact_info


@router.get("/stats")
def get_location_stats(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get location-based statistics for user's area"""
    if not current_user.latitude or not current_user.longitude:
        return {"message": "Set your location to see local statistics"}

    radius = current_user.search_radius or 25

    # Get all listings to calculate stats
    listings = (
        db.query(Listing)
        .filter(Listing.status == "active", Listing.location.isnot(None))
        .all()
    )

    local_listings = []
    for listing in listings:
        if (
            listing.location
            and listing.location.get("latitude")
            and listing.location.get("longitude")
        ):
            distance = LocationService.calculate_distance(
                current_user.latitude,
                current_user.longitude,
                float(listing.location["latitude"]),
                float(listing.location["longitude"]),
            )

            if distance <= radius:
                local_listings.append(listing)

    # Calculate statistics
    stats = {
        "total_local_listings": len(local_listings),
        "for_sale_count": len(
            [l for l in local_listings if l.listing_type == "for_sale"]
        ),
        "give_away_count": len(
            [l for l in local_listings if l.listing_type == "give_away"]
        ),
        "looking_for_count": len(
            [l for l in local_listings if l.listing_type == "looking_for"]
        ),
        "organic_count": len([l for l in local_listings if l.organic]),
        "search_radius": radius,
        "user_location": LocationService.format_location_display(current_user.location),
    }

    return stats
