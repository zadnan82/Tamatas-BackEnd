from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_, and_
from app.database import get_db
from app.models import User, Listing, Favorite
from app.schemas import ListingCreate, ListingUpdate, Listing as ListingSchema
from app.auth import get_current_active_user
from app.utils import generate_id

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/", response_model=ListingSchema)
def create_listing(
    listing: ListingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new listing"""
    try:
        db_listing = Listing(
            id=generate_id(), **listing.dict(), created_by=current_user.id, view_count=0
        )
        db.add(db_listing)
        db.commit()
        db.refresh(db_listing)

        # Load the owner relationship
        db_listing.owner = current_user

        return db_listing
    except Exception as e:
        db.rollback()
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
    sort_by: str = Query("created_date", regex="^(created_date|price|view_count)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get listings with filters and sorting"""
    try:
        # Start with active listings only
        query = db.query(Listing).filter(Listing.status == "active")

        # Join with owner for full data
        query = query.join(User, Listing.created_by == User.id)

        # Apply filters
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
            # Search in both city and state fields in the JSON location column
            location_filter = or_(
                func.lower(Listing.location["city"].astext).like(
                    f"%{location.lower()}%"
                ),
                func.lower(Listing.location["state"].astext).like(
                    f"%{location.lower()}%"
                ),
            )
            query = query.filter(location_filter)

        if organic_only:
            query = query.filter(Listing.organic == True)

        # Apply sorting
        sort_column = getattr(Listing, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Get results with pagination
        listings = query.offset(skip).limit(limit).all()

        return listings

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
def get_feeds(limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    """Get feed listings (popular and recent)"""
    try:
        # Get popular listings (high view count) from last 30 days
        from sqlalchemy import text

        popular_listings = (
            db.query(Listing)
            .join(User, Listing.created_by == User.id)
            .filter(
                Listing.status == "active",
                Listing.created_date >= func.now() - text("interval '30 days'"),
            )
            .order_by(desc(Listing.view_count))
            .limit(limit // 2)
            .all()
        )

        # Get recent listings
        recent_listings = (
            db.query(Listing)
            .join(User, Listing.created_by == User.id)
            .filter(Listing.status == "active")
            .order_by(desc(Listing.created_date))
            .limit(limit // 2)
            .all()
        )

        # Combine and remove duplicates
        all_listings = popular_listings + recent_listings
        unique_listings = list(
            {listing.id: listing for listing in all_listings}.values()
        )

        return unique_listings[:limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feeds: {str(e)}")


@router.get("/{listing_id}", response_model=ListingSchema)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    """Get a specific listing by ID"""
    try:
        listing = (
            db.query(Listing)
            .join(User, Listing.created_by == User.id)
            .filter(Listing.id == listing_id)
            .first()
        )

        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

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
def update_listing(
    listing_id: str,
    listing_update: ListingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update a listing"""
    try:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        if listing.created_by != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this listing"
            )

        # Update only provided fields
        for field, value in listing_update.dict(exclude_unset=True).items():
            setattr(listing, field, value)

        db.commit()
        db.refresh(listing)

        # Load the owner relationship
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
    db: Session = Depends(get_db),
):
    """Get listings by category"""
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
        return listings
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch listings by category: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=List[ListingSchema])
def get_user_listings(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get listings by a specific user"""
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        listings = (
            db.query(Listing)
            .filter(Listing.created_by == user_id, Listing.status == "active")
            .order_by(desc(Listing.created_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Set owner for each listing
        for listing in listings:
            listing.owner = user

        return listings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch user listings: {str(e)}"
        )


@router.post("/{listing_id}/view")
def increment_view_count(listing_id: str, db: Session = Depends(get_db)):
    """Increment view count for a listing"""
    try:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        listing.view_count = (listing.view_count or 0) + 1
        db.commit()

        return {"message": "View count updated", "view_count": listing.view_count}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update view count: {str(e)}"
        )


@router.get("/search/autocomplete")
def search_autocomplete(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get autocomplete suggestions for search"""
    try:
        # Search in titles and return unique suggestions
        suggestions = (
            db.query(Listing.title)
            .filter(Listing.status == "active", Listing.title.ilike(f"%{q}%"))
            .distinct()
            .limit(limit)
            .all()
        )

        return [suggestion[0] for suggestion in suggestions]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get autocomplete suggestions: {str(e)}"
        )


@router.get("/stats/overview")
def get_marketplace_stats(db: Session = Depends(get_db)):
    """Get marketplace statistics"""
    try:
        stats = {
            "total_listings": db.query(Listing)
            .filter(Listing.status == "active")
            .count(),
            "for_sale_count": db.query(Listing)
            .filter(Listing.status == "active", Listing.listing_type == "for_sale")
            .count(),
            "looking_for_count": db.query(Listing)
            .filter(Listing.status == "active", Listing.listing_type == "looking_for")
            .count(),
            "organic_count": db.query(Listing)
            .filter(Listing.status == "active", Listing.organic == True)
            .count(),
            "total_views": db.query(func.sum(Listing.view_count))
            .filter(Listing.status == "active")
            .scalar()
            or 0,
            "categories": db.query(
                Listing.category, func.count(Listing.id).label("count")
            )
            .filter(Listing.status == "active")
            .group_by(Listing.category)
            .all(),
        }

        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get marketplace stats: {str(e)}"
        )
