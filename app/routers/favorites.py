from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Favorite, Listing
from app.schemas import FavoriteCreate, Favorite as FavoriteSchema
from app.auth import get_current_active_user
from app.utils import generate_id

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/", response_model=FavoriteSchema)
def add_favorite(
    favorite: FavoriteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Check if listing exists
    listing = db.query(Listing).filter(Listing.id == favorite.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Check if already favorited
    existing_favorite = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.listing_id == favorite.listing_id,
        )
        .first()
    )

    if existing_favorite:
        raise HTTPException(status_code=400, detail="Listing already in favorites")

    db_favorite = Favorite(
        id=generate_id(), user_id=current_user.id, listing_id=favorite.listing_id
    )
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite


@router.get("/", response_model=List[FavoriteSchema])
def get_favorites(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    favorites = db.query(Favorite).filter(Favorite.user_id == current_user.id).all()
    return favorites


@router.delete("/{favorite_id}")
def remove_favorite(
    favorite_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    favorite = db.query(Favorite).filter(Favorite.id == favorite_id).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    if favorite.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to remove this favorite"
        )

    db.delete(favorite)
    db.commit()
    return {"message": "Favorite removed successfully"}
