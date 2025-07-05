# UPDATE app/routers/listings.py - Enhanced with location features

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from app.database import get_db
from app.models import User, Listing, Favorite
from app.schemas import (
    ListingCreate,
    ListingUpdate,
    Listing as ListingSchema,
    SearchFilters,
)
from app.auth import get_current_active_user
from app.utils import generate_id
from app.location_utils import LocationService

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/", response_model=ListingSchema)
async def create_listing(
    listing: ListingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new listing with mandatory location"""
    try:
        # Check if user has location set (required for creating listings)
        if not current_user.latitude or not current_user.longitude:
            raise HTTPException(
                status_code=400,
                detail="You must set your location before creating listings. Please update your profile.",
            )

        listing_data = listing.dict()

        # Validate location data
        if not listing_data.get("location"):
            raise HTTPException(
                status_code=400, detail="Location is required for all listings"
            )

        # Auto-geocode if location doesn't have coordinates
        if not listing_data["location"].get("latitude") or not listing_data[
            "location"
        ].get("longitude"):
            # Use user's location as fallback or try to geocode listing location
            listing_location = listing_data["location"]

            if listing_location.get("city") and listing_location.get("country"):
                # Try to geocode the specific listing location
                address_parts = []
                if listing_location.get("area"):
                    address_parts.append(listing_location["area"])
                if listing_location.get("city"):
                    address_parts.append(listing_location["city"])
                if listing_location.get("state"):
                    address_parts.append(listing_location["state"])
                if listing_location.get("country"):
                    address_parts.append(listing_location["country"])

                address = ", ".join(address_parts)
                geocoded = await LocationService.geocode_address(address)

                if geocoded:
                    listing_data["location"].update(
                        {
                            "latitude": geocoded["latitude"],
                            "longitude": geocoded["longitude"],
                            "formatted_address": geocoded.get("formatted_address"),
                        }
                    )
                else:
                    # Fallback to user's location
                    listing_data["location"].update(
                        {
                            "latitude": current_user.latitude,
                            "longitude": current_user.longitude,
                            "formatted_address": LocationService.format_location_display(
                                current_user.location
                            ),
                        }
                    )
            else:
                # Use user's location
                listing_data["location"] = current_user.location.copy()
                listing_data["location"].update(
                    {
                        "latitude": current_user.latitude,
                        "longitude": current_user.longitude,
                    }
                )

        # Validate price for sale listings
        if listing_data["listing_type"] == "for_sale" and (
            listing_data.get("price") is None or listing_data.get("price") <= 0
        ):
            raise HTTPException(
                status_code=400, detail="Price is required for sale listings"
            )

        # Set price to 0 for give_away listings
        if listing_data["listing_type"] == "give_away":
            listing_data["price"] = 0
            listing_data["price_unit"] = None

        db_listing = Listing(
            id=generate_id(), **listing_data, created_by=current_user.id, view_count=0
        )
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)

        db_listing.owner = current_user

        print(f"✅ Listing created: {db_listing.title} by {current_user.email}")
        return db_listing

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to create listing: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create listing: {str(e)}"
        )


@router.get("/", response_model=List[ListingSchema])
def get_listings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = None,
    listing_type: Optional[str] = None,
    search: Optional[str] = None,
    location: Optional[str] = None,
    organic_only: bool = False,
    near_me: bool = False,
    radius: int = Query(25, ge=1, le=200),
    sort_by: str = Query(
        "created_date", regex="^(created_date|price|view_count|distance)$"
    ),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Enhanced listing search with location filtering"""
    try:
        # Start with active listings only
        query = db.query(Listing).filter(Listing.status == "active")
        query = query.join(User, Listing.created_by == User.id)

        # Apply basic filters
        if category and category != "all":
            query = query.filter(Listing.category == category)

        if listing_type and listing_type != "all":
            query = query.filter(Listing.listing_type == listing_type)

        if search:
            search_filter = or_(
                Listing.title.ilike(f"%{search}%"),
                Listing.description.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)

        if location:
            location_filter = or_(
                func.lower(Listing.location["city"].as_string()).like(
                    f"%{location.lower()}%"
                ),
                func.lower(Listing.location["state"].as_string()).like(
                    f"%{location.lower()}%"
                ),
                func.lower(Listing.location["country"].as_string()).like(
                    f"%{location.lower()}%"
                ),
            )
            query = query.filter(location_filter)

        if organic_only:
            query = query.filter(Listing.organic == True)

        # Get all listings first for distance calculation
        all_listings = query.all()

        # Apply location-based filtering if requested
        filtered_listings = all_listings
        if (
            near_me
            and current_user
            and current_user.latitude
            and current_user.longitude
        ):
            filtered_listings = []
            for listing in all_listings:
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
                        listing.distance = distance  # Add distance for sorting
                        filtered_listings.append(listing)

        # Apply sorting
        if sort_by == "distance" and near_me:
            filtered_listings.sort(key=lambda x: getattr(x, "distance", float("inf")))
            if sort_order == "desc":
                filtered_listings.reverse()
        else:
            if sort_by == "created_date":
                filtered_listings.sort(
                    key=lambda x: x.created_date, reverse=(sort_order == "desc")
                )
            elif sort_by == "price":
                # Handle None prices (give_away items)
                filtered_listings.sort(
                    key=lambda x: x.price if x.price is not None else 0,
                    reverse=(sort_order == "desc"),
                )
            elif sort_by == "view_count":
                filtered_listings.sort(
                    key=lambda x: x.view_count, reverse=(sort_order == "desc")
                )

        # Apply pagination
        start = skip
        end = skip + limit
        paginated_listings = filtered_listings[start:end]

        return paginated_listings

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch listings: {str(e)}"
        )


@router.get("/my", response_model=List[ListingSchema])
def get_my_listings(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get current user's listings"""
    try:
        listings = (
            db.query(Listing)
            .filter(Listing.created_by == current_user.id)
            .order_by(desc(Listing.created_date))
            .all()
        )
        return listings
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch user listings: {str(e)}"
        )


@router.get("/feeds", response_model=List[ListingSchema])
def get_feeds(
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get feed listings prioritizing local content if user has location"""
    try:
        # Get recent listings
        recent_query = (
            db.query(Listing)
            .join(User, Listing.created_by == User.id)
            .filter(Listing.status == "active")
            .order_by(desc(Listing.created_date))
        )

        # If user has location, prioritize local content
        if current_user and current_user.latitude and current_user.longitude:
            all_recent = recent_query.limit(limit * 3).all()  # Get more to filter

            local_listings = []
            other_listings = []

            for listing in all_recent:
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

                    radius = current_user.search_radius or 50
                    if distance <= radius:
                        local_listings.append(listing)
                    else:
                        other_listings.append(listing)
                else:
                    other_listings.append(listing)

            # Combine local first, then others
            feed_listings = local_listings + other_listings
            return feed_listings[:limit]
        else:
            # No location, just return recent
            return recent_query.limit(limit).all()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feeds: {str(e)}")


@router.get("/{listing_id}", response_model=ListingSchema)
def get_listing(
    listing_id: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific listing by ID with distance info if user has location"""
    try:
        listing = (
            db.query(Listing)
            .join(User, Listing.created_by == User.id)
            .filter(Listing.id == listing_id)
            .first()
        )

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Add distance information if user has location
        if (
            current_user
            and current_user.latitude
            and current_user.longitude
            and listing.location
            and listing.location.get("latitude")
            and listing.location.get("longitude")
        ):
            distance = LocationService.calculate_distance(
                current_user.latitude,
                current_user.longitude,
                float(listing.location["latitude"]),
                float(listing.location["longitude"]),
            )
            listing.distance = round(distance, 1)

        # Increment view count
        listing.view_count = (listing.view_count or 0) + 1
        db.commit()

        return listing
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch listing: {str(e)}"
        )


@router.put("/{listing_id}", response_model=ListingSchema)
async def update_listing(
    listing_id: str,
    listing_update: ListingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a listing with location validation"""
    try:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        if listing.created_by != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this listing"
            )

        update_data = listing_update.dict(exclude_unset=True)

        # Handle location updates
        if "location" in update_data and update_data["location"]:
            location_data = update_data["location"]

            # Geocode if coordinates missing
            if not location_data.get("latitude") or not location_data.get("longitude"):
                if location_data.get("city") and location_data.get("country"):
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
                        location_data.update(
                            {
                                "latitude": geocoded["latitude"],
                                "longitude": geocoded["longitude"],
                                "formatted_address": geocoded.get("formatted_address"),
                            }
                        )

        # Validate price for listing type changes
        if "listing_type" in update_data:
            new_type = update_data["listing_type"]
            if new_type == "for_sale":
                current_price = update_data.get("price", listing.price)
                if current_price is None or current_price <= 0:
                    raise HTTPException(
                        status_code=400, detail="Price is required for sale listings"
                    )
            elif new_type == "give_away":
                update_data["price"] = 0

        # Update fields
        for field, value in update_data.items():
            setattr(listing, field, value)

        db.commit()
        db.refresh(listing)
        listing.owner = current_user

        return listing
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update listing: {str(e)}"
        )


@router.delete("/{listing_id}")
def delete_listing(
    listing_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a listing"""
    try:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        if listing.created_by != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this listing"
            )

        # Delete associated favorites first
        db.query(Favorite).filter(Favorite.listing_id == listing_id).delete()

        # Delete the listing
        db.delete(listing)
        db.commit()

        return {"message": "Listing deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to delete listing: {str(e)}"
        )


@router.get("/category/{category}", response_model=List[ListingSchema])
def get_listings_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get listings by category with distance info"""
    try:
        listings = (
            db.query(Listing)
            .join(User, Listing.created_by == User.id)
            .filter(Listing.status == "active", Listing.category == category)
            .order_by(desc(Listing.created_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Add distance if user has location
        if current_user and current_user.latitude and current_user.longitude:
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
                    listing.distance = round(distance, 1)

        return listings
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch listings by category: {str(e)}"
        )


@router.get("/stats/overview")
def get_marketplace_stats(
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get marketplace statistics with local stats if user has location"""
    try:
        # Global stats
        global_stats = {
            "total_listings": db.query(Listing)
            .filter(Listing.status == "active")
            .count(),
            "for_sale_count": db.query(Listing)
            .filter(Listing.status == "active", Listing.listing_type == "for_sale")
            .count(),
            "give_away_count": db.query(Listing)
            .filter(Listing.status == "active", Listing.listing_type == "give_away")
            .count(),
            "looking_for_count": db.query(Listing)
            .filter(Listing.status == "active", Listing.listing_type == "looking_for")
            .count(),
            "organic_count": db.query(Listing)
            .filter(Listing.status == "active", Listing.organic == True)
            .count(),
        }

        # Add local stats if user has location
        if current_user and current_user.latitude and current_user.longitude:
            # Get all listings to calculate local stats
            all_listings = db.query(Listing).filter(Listing.status == "active").all()

            local_listings = []
            radius = current_user.search_radius or 25

            for listing in all_listings:
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

            local_stats = {
                "local_total": len(local_listings),
                "local_for_sale": len(
                    [l for l in local_listings if l.listing_type == "for_sale"]
                ),
                "local_give_away": len(
                    [l for l in local_listings if l.listing_type == "give_away"]
                ),
                "local_looking_for": len(
                    [l for l in local_listings if l.listing_type == "looking_for"]
                ),
                "local_organic": len([l for l in local_listings if l.organic]),
                "search_radius": radius,
                "user_location": LocationService.format_location_display(
                    current_user.location
                ),
            }

            global_stats.update(local_stats)

        return global_stats

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get marketplace stats: {str(e)}"
        )


print("✅ Enhanced listings router loaded with location features")
