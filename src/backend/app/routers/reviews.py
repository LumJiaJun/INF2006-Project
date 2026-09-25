import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api", tags=["reviews"])
logger = logging.getLogger("staysphere.reviews")


@router.post("/reviews", response_model=schemas.ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    booking = db.query(models.Booking).filter(models.Booking.booking_id == payload.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.guest_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only review your own bookings")
    if booking.status == models.BookingStatus.cancelled:
        raise HTTPException(status_code=400, detail="Cannot review a cancelled booking")

    checkout = booking.check_out.replace(tzinfo=timezone.utc) if booking.check_out.tzinfo is None else booking.check_out
    if checkout > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="You can only review a booking after your stay has ended")

    existing = db.query(models.Review).filter(models.Review.booking_id == payload.booking_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this booking")

    review = models.Review(
        booking_id=booking.booking_id,
        listing_id=booking.listing_id,
        guest_id=current_user.user_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    logger.info("review_created review_id=%s listing_id=%s guest_id=%s rating=%s",
                review.review_id, booking.listing_id, current_user.user_id, payload.rating)

    return schemas.ReviewOut(
        review_id=review.review_id, booking_id=review.booking_id, listing_id=review.listing_id,
        guest_id=review.guest_id, guest_name=current_user.name, rating=review.rating,
        comment=review.comment, created_at=review.created_at,
    )


@router.get("/listings/{listing_id}/reviews", response_model=list[schemas.ReviewOut])
def get_listing_reviews(listing_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Review, models.User)
        .join(models.User, models.Review.guest_id == models.User.user_id)
        .filter(models.Review.listing_id == listing_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )
    return [
        schemas.ReviewOut(
            review_id=r.review_id, booking_id=r.booking_id, listing_id=r.listing_id,
            guest_id=r.guest_id, guest_name=u.name, rating=r.rating,
            comment=r.comment, created_at=r.created_at,
        )
        for r, u in rows
    ]
