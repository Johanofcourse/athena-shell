from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Listing
from app.schemas import ListingDetailOut, ListingOut

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("", response_model=list[ListingOut])
def list_listings(limit: int = 50, db: Session = Depends(get_db)) -> list[Listing]:
    limit = max(1, min(limit, 200))
    stmt = select(Listing).order_by(Listing.last_event_date.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


@router.get("/{listing_id}", response_model=ListingDetailOut)
def get_listing(listing_id: str, db: Session = Depends(get_db)) -> Listing:
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
