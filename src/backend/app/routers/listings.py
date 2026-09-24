import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["listings"])

# --- Scalability mechanism: simple in-process TTL cache -------------
# The /analytics/overview endpoint runs several aggregate queries over
# the full listings table. Under load, every dashboard view would
# re-run those aggregates. Caching the result for a short TTL trades a
# small staleness window for a large reduction in DB load, which is
# the same idea as a Redis/CDN cache layer at larger scale (documented
# in docs/ARCHITECTURE.md and tested in tests/04_scalability_resilience).
_analytics_cache = {"data": None, "expires_at": 0.0}
_CACHE_TTL_SECONDS = 30

SORT_OPTIONS = {
    "price_asc": (models.Listing.price, "asc"),
    "price_desc": (models.Listing.price, "desc"),
    "rating": (models.Listing.review_scores_rating, "desc"),
}


@router.get("/listings", response_model=schemas.ListingSearchResult)
def search_listings(
    city: Optional[str] = None,
    room_type: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    accommodates: Optional[int] = Query(None, ge=1),
    instant_bookable: Optional[bool] = None,
    sort: str = Query("recommended"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    # NOTE: SQLAlchemy's query builder parameterizes all values below,
    # so user input can never be concatenated into raw SQL. This is
    # the primary SQL-injection control for this endpoint.
    query = db.query(models.Listing)

    if city:
        query = query.filter(models.Listing.city == city)
    if room_type:
        query = query.filter(models.Listing.room_type == room_type)
    if property_type:
        query = query.filter(models.Listing.property_type == property_type)
    if min_price is not None:
        query = query.filter(models.Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Listing.price <= max_price)
    if min_rating is not None:
        query = query.filter(models.Listing.review_scores_rating >= min_rating)
    if accommodates is not None:
        query = query.filter(models.Listing.accommodates >= accommodates)
    if instant_bookable is not None:
        query = query.filter(models.Listing.instant_bookable == instant_bookable)

    total = query.count()

    if sort in SORT_OPTIONS:
        column, direction = SORT_OPTIONS[sort]
        query = query.order_by(column.desc() if direction == "desc" else column.asc())
    else:
        # "recommended": rating desc as a simple relevance proxy
        query = query.order_by(models.Listing.review_scores_rating.desc())

    results = query.offset((page - 1) * page_size).limit(page_size).all()

    return schemas.ListingSearchResult(total=total, page=page, page_size=page_size, results=results)


@router.get("/listings/{listing_id}", response_model=schemas.ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("/listings/{listing_id}/availability", response_model=schemas.AvailabilityResponse)
def listing_availability(listing_id: int, db: Session = Depends(get_db)):
    """
    Public endpoint: which date ranges are already booked for this
    listing, so the frontend can grey them out on the booking calendar
    before the guest even tries to submit — the server-side overlap
    check in bookings.py is still the real enforcement, this just
    surfaces the same information visually ahead of time.
    """
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    bookings = (
        db.query(models.Booking)
        .filter(
            models.Booking.listing_id == listing_id,
            models.Booking.status.in_([models.BookingStatus.pending, models.BookingStatus.confirmed]),
        )
        .all()
    )
    return schemas.AvailabilityResponse(
        listing_id=listing_id,
        minimum_nights=listing.minimum_nights,
        maximum_nights=listing.maximum_nights,
        booked_ranges=[schemas.BookedRange(check_in=b.check_in, check_out=b.check_out) for b in bookings],
    )


@router.get("/analytics/overview", response_model=schemas.AnalyticsOverview)
def analytics_overview(db: Session = Depends(get_db)):
    from sqlalchemy import func

    now = time.time()
    if _analytics_cache["data"] is not None and now < _analytics_cache["expires_at"]:
        return _analytics_cache["data"]

    total = db.query(func.count(models.Listing.listing_id)).scalar() or 0
    avg_price = db.query(func.avg(models.Listing.price)).scalar() or 0
    avg_rating = db.query(func.avg(models.Listing.review_scores_rating)).scalar() or 0

    prices = [p[0] for p in db.query(models.Listing.price).order_by(models.Listing.price).all()]
    median_price = prices[len(prices) // 2] if prices else 0

    room_type_row = (
        db.query(models.Listing.room_type, func.count(models.Listing.listing_id))
        .group_by(models.Listing.room_type)
        .order_by(func.count(models.Listing.listing_id).desc())
        .first()
    )
    city_row = (
        db.query(models.Listing.city, func.count(models.Listing.listing_id))
        .group_by(models.Listing.city)
        .order_by(func.count(models.Listing.listing_id).desc())
        .first()
    )

    result = schemas.AnalyticsOverview(
        total_listings=total,
        average_price=round(avg_price, 2),
        median_price=round(median_price, 2),
        average_rating=round(avg_rating, 2),
        most_common_room_type=room_type_row[0] if room_type_row else "N/A",
        most_common_city=city_row[0] if city_row else "N/A",
    )
    _analytics_cache["data"] = result
    _analytics_cache["expires_at"] = now + _CACHE_TTL_SECONDS
    return result
