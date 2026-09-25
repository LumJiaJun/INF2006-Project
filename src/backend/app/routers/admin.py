import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas, auth, admin_schemas, pricing
from ..database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger("staysphere.admin")

require_admin = auth.require_role("admin")


@router.get("/listings", response_model=schemas.ListingSearchResult)
def admin_list_listings(
    page: int = 1,
    page_size: int = 20,
    city: str | None = None,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    query = db.query(models.Listing).order_by(models.Listing.listing_id.asc())
    if city:
        query = query.filter(models.Listing.city == city)
    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()
    return schemas.ListingSearchResult(total=total, page=page, page_size=page_size, results=results)


@router.get("/listings-pricing", response_model=list[admin_schemas.AdminListingOut])
def admin_listings_pricing(
    page: int = 1,
    page_size: int = 20,
    city: str | None = None,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """
    Same page of listings as /listings, but each row also carries the
    trained model's "suggested" fair price and the gap versus the
    listing's actual price, so an admin can spot under/overpriced
    listings at a glance. This is the "price automation" surfaced to
    admins — a per-listing suggestion, not an automatic price change.
    """
    query = db.query(models.Listing).order_by(models.Listing.listing_id.asc())
    if city:
        query = query.filter(models.Listing.city == city)
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    out = []
    for listing in rows:
        try:
            suggested = pricing.estimate_price(
                city=listing.city,
                property_type=listing.property_type,
                room_type=listing.room_type,
                accommodates=listing.accommodates,
                bedrooms=listing.bedrooms,
                minimum_nights=listing.minimum_nights,
                review_scores_rating=listing.review_scores_rating or 4.0,
            )
            gap_pct = round((listing.price - suggested) / suggested * 100, 1) if suggested else None
        except HTTPException:
            suggested, gap_pct = None, None  # model not trained yet — degrade gracefully

        data = admin_schemas.AdminListingOut.model_validate(listing).model_dump()
        data["suggested_price"] = suggested
        data["price_gap_pct"] = gap_pct
        out.append(admin_schemas.AdminListingOut(**data))
    return out


@router.post("/listings", response_model=schemas.ListingOut, status_code=201)
def admin_create_listing(
    payload: admin_schemas.ListingCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    max_id = db.query(func.max(models.Listing.listing_id)).scalar() or 0
    listing = models.Listing(listing_id=max_id + 1, **payload.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    logger.info("admin_listing_created listing_id=%s by_admin_id=%s", listing.listing_id, admin.user_id)
    return listing


@router.patch("/listings/{listing_id}", response_model=schemas.ListingOut)
def admin_update_listing(
    listing_id: int,
    payload: admin_schemas.ListingUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)
    db.commit()
    db.refresh(listing)
    logger.info("admin_listing_updated listing_id=%s by_admin_id=%s", listing_id, admin.user_id)
    return listing


@router.delete("/listings/{listing_id}", status_code=204)
def admin_delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    active_bookings = (
        db.query(models.Booking)
        .filter(
            models.Booking.listing_id == listing_id,
            models.Booking.status.in_([models.BookingStatus.pending, models.BookingStatus.confirmed]),
        )
        .count()
    )
    if active_bookings > 0:
        raise HTTPException(status_code=409, detail="Cannot delete a listing with active bookings")
    db.delete(listing)
    db.commit()
    logger.info("admin_listing_deleted listing_id=%s by_admin_id=%s", listing_id, admin.user_id)
    return None


@router.get("/analytics", response_model=admin_schemas.AdminAnalytics)
def admin_analytics(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    total_listings = db.query(func.count(models.Listing.listing_id)).scalar() or 0
    total_users = db.query(func.count(models.User.user_id)).scalar() or 0
    total_bookings = db.query(func.count(models.Booking.booking_id)).scalar() or 0
    confirmed_bookings = (
        db.query(func.count(models.Booking.booking_id))
        .filter(models.Booking.status == models.BookingStatus.confirmed)
        .scalar() or 0
    )
    cancelled_bookings = (
        db.query(func.count(models.Booking.booking_id))
        .filter(models.Booking.status == models.BookingStatus.cancelled)
        .scalar() or 0
    )
    total_revenue = (
        db.query(func.coalesce(func.sum(models.Booking.total_amount), 0.0))
        .filter(models.Booking.status.in_([models.BookingStatus.confirmed, models.BookingStatus.completed]))
        .scalar() or 0.0
    )
    avg_price = db.query(func.avg(models.Listing.price)).scalar() or 0
    avg_rating = db.query(func.avg(models.Listing.review_scores_rating)).scalar() or 0
    city_row = (
        db.query(models.Listing.city, func.count(models.Listing.listing_id))
        .group_by(models.Listing.city)
        .order_by(func.count(models.Listing.listing_id).desc())
        .first()
    )

    return admin_schemas.AdminAnalytics(
        total_listings=total_listings,
        total_users=total_users,
        total_bookings=total_bookings,
        confirmed_bookings=confirmed_bookings,
        cancelled_bookings=cancelled_bookings,
        total_revenue=round(total_revenue, 2),
        average_price=round(avg_price, 2),
        average_rating=round(avg_rating, 2),
        most_common_city=city_row[0] if city_row else "N/A",
    )


@router.get("/bookings", response_model=list[admin_schemas.AdminBookingOut])
def admin_list_bookings(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """
    Lets an admin see every booking guests have made, proving the
    booking workflow actually writes to the shared database rather
    than just a guest's own session.
    """
    rows = (
        db.query(models.Booking, models.Listing, models.User)
        .join(models.Listing, models.Booking.listing_id == models.Listing.listing_id)
        .join(models.User, models.Booking.guest_id == models.User.user_id)
        .order_by(models.Booking.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [
        admin_schemas.AdminBookingOut(
            booking_id=b.booking_id,
            listing_id=b.listing_id,
            listing_name=l.name,
            guest_id=u.user_id,
            guest_name=u.name,
            guest_email=u.email,
            check_in=b.check_in.isoformat(),
            check_out=b.check_out.isoformat(),
            guests=b.guests,
            nights=b.nights,
            total_amount=b.total_amount,
            status=b.status,
            created_at=b.created_at.isoformat(),
        )
        for b, l, u in rows
    ]


@router.get("/pricing-insights", response_model=admin_schemas.PricingInsightsResponse)
def admin_pricing_insights(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """
    Per-city aggregate view standing in for a geographic demand/price
    heatmap. A true geospatial heatmap (rendered on a map) was
    descoped as more than this project needs; this gives the same
    underlying signal (which cities are priced high / booked a lot)
    in a form the frontend renders as colour-intensity bars.
    """
    rows = (
        db.query(
            models.Listing.city,
            func.count(models.Listing.listing_id),
            func.avg(models.Listing.price),
            func.avg(models.Listing.review_scores_rating),
            func.avg(models.Listing.latitude),
            func.avg(models.Listing.longitude),
        )
        .group_by(models.Listing.city)
        .all()
    )

    booking_counts = dict(
        db.query(models.Listing.city, func.count(models.Booking.booking_id))
        .join(models.Booking, models.Booking.listing_id == models.Listing.listing_id)
        .group_by(models.Listing.city)
        .all()
    )

    cities = []
    for city, count, avg_price, avg_rating, avg_lat, avg_lng in rows:
        cities.append({
            "city": city,
            "listing_count": count,
            "average_price": round(avg_price or 0, 2),
            "average_rating": round(avg_rating or 0, 2),
            "total_bookings": booking_counts.get(city, 0),
            "latitude": round(avg_lat or 0, 4),
            "longitude": round(avg_lng or 0, 4),
        })

    max_bookings = max([c["total_bookings"] for c in cities], default=0) or 1
    result_cities = [
        admin_schemas.CityInsight(
            **c,
            demand_index=round(c["total_bookings"] / max_bookings, 2),
        )
        for c in sorted(cities, key=lambda c: c["average_price"], reverse=True)
    ]

    # Neighbourhood-level breakdown — finer geographic detail than the
    # city-level bars, since "different locations" within one city can
    # have very different pricing.
    nb_rows = (
        db.query(
            models.Listing.city,
            models.Listing.neighbourhood,
            func.count(models.Listing.listing_id),
            func.avg(models.Listing.price),
            func.avg(models.Listing.review_scores_rating),
            func.avg(models.Listing.latitude),
            func.avg(models.Listing.longitude),
        )
        .group_by(models.Listing.city, models.Listing.neighbourhood)
        .all()
    )
    nb_booking_counts = dict(
        db.query(models.Listing.neighbourhood, func.count(models.Booking.booking_id))
        .join(models.Booking, models.Booking.listing_id == models.Listing.listing_id)
        .group_by(models.Listing.neighbourhood)
        .all()
    )
    neighbourhoods = []
    for city, nb, count, avg_price, avg_rating, avg_lat, avg_lng in nb_rows:
        neighbourhoods.append({
            "city": city,
            "neighbourhood": nb,
            "listing_count": count,
            "average_price": round(avg_price or 0, 2),
            "average_rating": round(avg_rating or 0, 2),
            "total_bookings": nb_booking_counts.get(nb, 0),
            "latitude": round(avg_lat or 0, 4),
            "longitude": round(avg_lng or 0, 4),
        })
    max_nb_bookings = max([n["total_bookings"] for n in neighbourhoods], default=0) or 1
    result_neighbourhoods = [
        admin_schemas.LocationInsight(**n, demand_index=round(n["total_bookings"] / max_nb_bookings, 2))
        for n in sorted(neighbourhoods, key=lambda n: n["average_price"], reverse=True)
    ]

    return admin_schemas.PricingInsightsResponse(
        cities=result_cities,
        neighbourhoods=result_neighbourhoods,
        note=(
            "Demand index is bookings-in-this-dataset relative to the busiest city/"
            "neighbourhood, not real market demand. Treat as an illustrative signal, "
            "not a pricing guarantee — see docs/RESPONSIBLE_AI.md."
        ),
    )


@router.get("/listings/{listing_id}/bookings", response_model=list[admin_schemas.AdminBookingOut])
def admin_listing_bookings(
    listing_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    """Per-listing booking calendar data — every booking (any status) for one listing."""
    rows = (
        db.query(models.Booking, models.Listing, models.User)
        .join(models.Listing, models.Booking.listing_id == models.Listing.listing_id)
        .join(models.User, models.Booking.guest_id == models.User.user_id)
        .filter(models.Booking.listing_id == listing_id)
        .order_by(models.Booking.check_in.asc())
        .all()
    )
    return [
        admin_schemas.AdminBookingOut(
            booking_id=b.booking_id, listing_id=b.listing_id, listing_name=l.name,
            guest_id=u.user_id, guest_name=u.name, guest_email=u.email,
            check_in=b.check_in.isoformat(), check_out=b.check_out.isoformat(),
            guests=b.guests, nights=b.nights, total_amount=b.total_amount,
            status=b.status, created_at=b.created_at.isoformat(),
        )
        for b, l, u in rows
    ]


@router.get("/reviews", response_model=list[admin_schemas.AdminReviewOut])
def admin_list_reviews(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    rows = (
        db.query(models.Review, models.Listing, models.User)
        .join(models.Listing, models.Review.listing_id == models.Listing.listing_id)
        .join(models.User, models.Review.guest_id == models.User.user_id)
        .order_by(models.Review.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [
        admin_schemas.AdminReviewOut(
            review_id=r.review_id, booking_id=r.booking_id, listing_id=r.listing_id,
            listing_name=l.name, guest_name=u.name, guest_email=u.email,
            rating=r.rating, comment=r.comment, created_at=r.created_at.isoformat(),
        )
        for r, l, u in rows
    ]


@router.delete("/reviews/{review_id}", status_code=204)
def admin_delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    review = db.query(models.Review).filter(models.Review.review_id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
    logger.info("admin_review_deleted review_id=%s by_admin_id=%s", review_id, admin.user_id)
    return None


@router.get("/users", response_model=list[admin_schemas.AdminUserOut])
def admin_list_users(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    users = (
        db.query(models.User)
        .order_by(models.User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    booking_counts = dict(
        db.query(models.Booking.guest_id, func.count(models.Booking.booking_id))
        .group_by(models.Booking.guest_id)
        .all()
    )
    return [
        admin_schemas.AdminUserOut(
            user_id=u.user_id, name=u.name, email=u.email, role=u.role,
            created_at=u.created_at.isoformat(), booking_count=booking_counts.get(u.user_id, 0),
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=admin_schemas.AdminUserOut)
def admin_update_user(
    user_id: int,
    payload: admin_schemas.AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        if payload.role not in ("guest", "host", "admin"):
            raise HTTPException(status_code=422, detail="role must be guest, host or admin")
        if user.user_id == admin.user_id and payload.role != "admin":
            raise HTTPException(status_code=400, detail="You cannot demote your own account")
        user.role = payload.role
    db.commit()
    db.refresh(user)
    booking_count = db.query(func.count(models.Booking.booking_id)).filter(models.Booking.guest_id == user.user_id).scalar() or 0
    logger.info("admin_user_updated user_id=%s by_admin_id=%s", user_id, admin.user_id)
    return admin_schemas.AdminUserOut(
        user_id=user.user_id, name=user.name, email=user.email, role=user.role,
        created_at=user.created_at.isoformat(), booking_count=booking_count,
    )


@router.delete("/users/{user_id}", status_code=204)
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    if user_id == admin.user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    active_bookings = (
        db.query(models.Booking)
        .filter(
            models.Booking.guest_id == user_id,
            models.Booking.status.in_([models.BookingStatus.pending, models.BookingStatus.confirmed]),
        )
        .count()
    )
    if active_bookings > 0:
        raise HTTPException(status_code=409, detail="Cannot delete a user with active bookings")
    db.delete(user)
    db.commit()
    logger.info("admin_user_deleted user_id=%s by_admin_id=%s", user_id, admin.user_id)
    return None
