from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, or_
from app.database import get_db
from app.models import User, Listing, Favorite
from app.schemas import ListingCreate, ListingUpdate, Listing as ListingSchema
from app.auth import get_current_active_user
from app.utils import generate_id
from app.tasks import update_listing_views

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/", response_model=ListingSchema)
def create_listing(
    listing: ListingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    db_listing = Listing(id=generate_id(), **listing.dict(), created_by=current_user.id)
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing


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
    query = db.query(Listing).filter(Listing.status == "active")

    # Apply filters
    if category and category != "all":
        query = query.filter(Listing.category == category)

    if listing_type and listing_type != "all":
        query = query.filter(Listing.listing_type == listing_type)

    if search:
        query = query.filter(
            or_(
                Listing.title.ilike(f"%{search}%"),
                Listing.description.ilike(f"%{search}%"),
            )
        )

    if location:
        query = query.filter(Listing.location["city"].astext.ilike(f"%{location}%"))

    if organic_only:
        query = query.filter(Listing.organic == True)

    # Apply sorting
    if sort_order == "desc":
        query = query.order_by(desc(getattr(Listing, sort_by)))
    else:
        query = query.order_by(asc(getattr(Listing, sort_by)))

    listings = query.offset(skip).limit(limit).all()
    return listings


@router.get("/my", response_model=List[ListingSchema])
def get_my_listings(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    listings = db.query(Listing).filter(Listing.created_by == current_user.id).all()
    return listings


@router.get("/feeds", response_model=List[ListingSchema])
def get_feeds(limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db)):
    # Get popular listings (high view count) and recent listings
    popular_listings = (
        db.query(Listing)
        .filter(Listing.status == "active")
        .order_by(desc(Listing.view_count))
        .limit(limit // 2)
        .all()
    )

    recent_listings = (
        db.query(Listing)
        .filter(Listing.status == "active")
        .order_by(desc(Listing.created_date))
        .limit(limit // 2)
        .all()
    )

    # Combine and remove duplicates
    all_listings = popular_listings + recent_listings
    unique_listings = list({listing.id: listing for listing in all_listings}.values())

    return unique_listings[:limit]


@router.get("/{listing_id}", response_model=ListingSchema)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Update view count asynchronously
    update_listing_views.delay(listing_id)

    return listing


@router.put("/{listing_id}", response_model=ListingSchema)
def update_listing(
    listing_id: str,
    listing_update: ListingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.created_by != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this listing"
        )

    for field, value in listing_update.dict(exclude_unset=True).items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}")
def delete_listing(
    listing_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.created_by != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this listing"
        )

    db.delete(listing)
    db.commit()
    return {"message": "Listing deleted successfully"}
