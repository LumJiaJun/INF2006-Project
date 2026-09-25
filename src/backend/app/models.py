import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, enum.Enum):
    guest = "guest"
    host = "host"
    admin = "admin"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.guest, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    bookings = relationship("Booking", back_populates="guest")


class Listing(Base):
    __tablename__ = "listings_source"

    listing_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    host_id = Column(Integer, index=True)
    host_since = Column(String)
    host_location = Column(String)
    host_response_time = Column(String)
    host_response_rate = Column(Integer)
    host_acceptance_rate = Column(Integer)
    host_is_superhost = Column(Boolean, default=False)
    host_total_listings_count = Column(Integer)
    host_has_profile_pic = Column(Boolean, default=True)
    host_identity_verified = Column(Boolean, default=False)
    neighbourhood = Column(String, index=True)
    district = Column(String)
    city = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    property_type = Column(String, index=True)
    room_type = Column(String, index=True)
    accommodates = Column(Integer)
    bedrooms = Column(Integer)
    amenities = Column(String)
    price = Column(Float, index=True)
    minimum_nights = Column(Integer)
    maximum_nights = Column(Integer)
    review_scores_rating = Column(Float, index=True)
    review_scores_accuracy = Column(Float)
    review_scores_cleanliness = Column(Float)
    review_scores_checkin = Column(Float)
    review_scores_communication = Column(Float)
    review_scores_location = Column(Float)
    review_scores_value = Column(Float)
    instant_bookable = Column(Boolean, default=False)

    bookings = relationship("Booking", back_populates="listing")


class Booking(Base):
    __tablename__ = "bookings"

    booking_id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings_source.listing_id"), nullable=False, index=True)
    guest_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    guests = Column(Integer, nullable=False)
    nights = Column(Integer, nullable=False)
    nightly_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.confirmed, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    listing = relationship("Listing", back_populates="bookings")
    guest = relationship("User", back_populates="bookings")

    __table_args__ = (
        Index("ix_booking_listing_dates", "listing_id", "check_in", "check_out"),
    )


class Review(Base):
    __tablename__ = "application_reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"), nullable=False, unique=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings_source.listing_id"), nullable=False, index=True)
    guest_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    booking = relationship("Booking")
    listing = relationship("Listing")
    guest = relationship("User")
