import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/bookings", tags=["bookings"])
logger = logging.getLogger("staysphere.bookings")


@router.post("", response_model=schemas.BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    listing = db.query(models.Listing).filter(models.Listing.listing_id == payload.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Nights are calendar nights (date difference), not the raw
    # timedelta, so a 2pm check-in to an 11am check-out four days
    # later still counts as the correct number of nights regardless
    # of the specific check-in/check-out times of day.
    nights = (payload.check_out.date() - payload.check_in.date()).days
    if nights < 1:
        raise HTTPException(status_code=400, detail="Stay must be at least 1 night")
    if nights < listing.minimum_nights:
        raise HTTPException(status_code=400, detail=f"Minimum stay is {listing.minimum_nights} nights")
    if listing.maximum_nights and nights > listing.maximum_nights:
        raise HTTPException(status_code=400, detail=f"Maximum stay is {listing.maximum_nights} nights")
    if payload.guests > listing.accommodates:
        raise HTTPException(status_code=400, detail=f"Listing accommodates at most {listing.accommodates} guests")

    # Conflict check: any existing confirmed booking for this listing
    # that overlaps the requested date range blocks the new booking.
    # This runs inside the same DB transaction as the insert below, so
    # two near-simultaneous requests cannot both slip past the check
    # (the second commit will still fail the unique constraint window
    # under concurrent load — see docs/DATABASE_SCHEMA.md).
    overlap = (
        db.query(models.Booking)
        .filter(
            models.Booking.listing_id == payload.listing_id,
            models.Booking.status.in_([models.BookingStatus.pending, models.BookingStatus.confirmed]),
            models.Booking.check_in < payload.check_out,
            models.Booking.check_out > payload.check_in,
        )
        .first()
    )
    if overlap:
        raise HTTPException(status_code=409, detail="Listing is not available for the selected dates")

    total_amount = round(nights * listing.price, 2)

    booking = models.Booking(
        listing_id=listing.listing_id,
        guest_id=current_user.user_id,
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        nights=nights,
        nightly_price=listing.price,
        total_amount=total_amount,
        status=models.BookingStatus.confirmed,
    )

    try:
        db.add(booking)
        db.commit()
        db.refresh(booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Booking conflict, please try different dates")

    logger.info("booking_created booking_id=%s listing_id=%s guest_id=%s", booking.booking_id, listing.listing_id, current_user.user_id)
    return booking


@router.get("", response_model=list[schemas.BookingOut])
def my_trips(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    bookings = (
        db.query(models.Booking)
        .filter(models.Booking.guest_id == current_user.user_id)
        .order_by(models.Booking.check_in.desc())
        .all()
    )

    reviewed_booking_ids = set(
        b_id for (b_id,) in db.query(models.Review.booking_id)
        .filter(models.Review.booking_id.in_([b.booking_id for b in bookings]))
        .all()
    )

    now = datetime.now(timezone.utc)
    out = []
    for b in bookings:
        data = schemas.BookingOut.model_validate(b).model_dump()
        has_review = b.booking_id in reviewed_booking_ids
        checkout_naive = b.check_out.replace(tzinfo=timezone.utc) if b.check_out.tzinfo is None else b.check_out
        can_review = (
            not has_review
            and b.status != models.BookingStatus.cancelled
            and checkout_naive <= now
        )
        data["has_review"] = has_review
        data["can_review"] = can_review
        out.append(schemas.BookingOut(**data))
    return out


@router.patch("/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    booking = db.query(models.Booking).filter(models.Booking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    # Authorization: a guest may only cancel their own booking.
    if booking.guest_id != current_user.user_id and current_user.role != models.UserRole.admin:
        raise HTTPException(status_code=403, detail="You cannot cancel someone else's booking")
    if booking.status == models.BookingStatus.cancelled:
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    booking.status = models.BookingStatus.cancelled
    db.commit()
    db.refresh(booking)
    logger.info("booking_cancelled booking_id=%s by_user_id=%s", booking.booking_id, current_user.user_id)
    return booking
