"""
Loads listing data from a CSV into the listings_source table, and
creates demo accounts for grading/demo purposes:

    Guest demo login:  guest@staysphere.demo  / Demo1234!
    Admin demo login:  admin@staysphere.demo  / Demo1234!

Usage:
    python -m app.seed                     # uses data/sample/dummy_listings.csv
    python -m app.seed /path/to/real.csv   # uses a different file (e.g. real dataset)
"""
import sys
import os
import csv
from collections import defaultdict
from datetime import datetime, timezone

from .database import Base, engine, SessionLocal
from . import models, auth

DEFAULT_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "raw", "Listings.csv"
)
DEFAULT_REVIEWS_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "raw", "Reviews.csv"
)

DEMO_PASSWORD = "Demo1234!"
HISTORICAL_REVIEWS_PER_LISTING = 3


def clean_value(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if not value or value.lower() in {"nan", "none", "null", "n/a"} else value


def str_to_bool(value: str) -> bool:
    return str(clean_value(value) or "").lower() in ("true", "1", "yes", "t")


def to_int(value, default=0):
    value = clean_value(value)
    if value is None:
        return default
    try:
        return int(float(value.replace(",", "")))
    except ValueError:
        return default


def to_float(value, default=None):
    value = clean_value(value)
    if value is None:
        return default
    try:
        return float(value.replace(",", "").replace("$", ""))
    except ValueError:
        return default


def rating_to_five(value):
    rating = to_float(value)
    if rating is None:
        return None
    if rating > 5:
        rating /= 20
    return max(0.0, min(5.0, rating))


def subscore_to_five(value):
    score = to_float(value)
    if score is None:
        return None
    if score > 5:
        score /= 2
    return max(0.0, min(5.0, score))


def parse_date(value, default):
    value = clean_value(value)
    if not value:
        return default
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(value[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return default


def seed_demo_users(db):
    demo_accounts = [
        ("Demo Guest", "guest@staysphere.demo", models.UserRole.guest),
        ("Demo Admin", "admin@staysphere.demo", models.UserRole.admin),
    ]
    for name, email, role in demo_accounts:
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            continue
        db.add(models.User(
            name=name,
            email=email,
            password_hash=auth.hash_password(DEMO_PASSWORD),
            role=role,
        ))
    db.commit()
    print(f"Demo accounts ready: guest@staysphere.demo / admin@staysphere.demo (password: {DEMO_PASSWORD})")


def seed_historical_reviews(db, csv_path):
    if not os.path.exists(csv_path) or db.query(models.HistoricalReview).count() > 0:
        return 0

    listing_ratings = {
        listing_id: rating or 4.0
        for listing_id, rating in db.query(
            models.Listing.listing_id, models.Listing.review_scores_rating
        ).all()
    }
    imported_per_listing = defaultdict(int)
    batch = []
    imported = 0

    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            listing_id = to_int(row.get("listing_id"), default=None)
            review_id = to_int(row.get("review_id"), default=None)
            reviewer_id = to_int(row.get("reviewer_id"), default=None)
            if listing_id not in listing_ratings or review_id is None or reviewer_id is None:
                continue
            if imported_per_listing[listing_id] >= HISTORICAL_REVIEWS_PER_LISTING:
                continue

            batch.append({
                "review_id": review_id,
                "listing_id": listing_id,
                "reviewer_id": reviewer_id,
                "rating": max(1, min(5, round(listing_ratings[listing_id]))),
                "created_at": parse_date(
                    row.get("date"), datetime(2020, 1, 1, tzinfo=timezone.utc)
                ),
            })
            imported_per_listing[listing_id] += 1
            imported += 1
            if len(batch) >= 5000:
                db.bulk_insert_mappings(models.HistoricalReview, batch)
                batch.clear()

    if batch:
        db.bulk_insert_mappings(models.HistoricalReview, batch)
    db.commit()
    return imported


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    csv_path = os.path.abspath(csv_path)

    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing = db.query(models.Listing).count()
    if existing > 0:
        print(f"listings_source already has {existing} rows. Skipping listing seed (delete staysphere.db to reseed).")
        seed_demo_users(db)
        imported_reviews = seed_historical_reviews(db, os.path.abspath(DEFAULT_REVIEWS_CSV))
        if imported_reviews:
            print(f"Imported {imported_reviews} historical reviews")
        db.close()
        return

    count = 0
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            listing = models.Listing(
                listing_id=to_int(row["listing_id"]),
                name=clean_value(row.get("name")) or "Airbnb listing",
                host_id=to_int(row.get("host_id"), default=None),
                host_since=clean_value(row.get("host_since")),
                host_location=clean_value(row.get("host_location")),
                host_response_time=clean_value(row.get("host_response_time")),
                host_response_rate=to_int(row.get("host_response_rate"), default=None),
                host_acceptance_rate=to_int(row.get("host_acceptance_rate"), default=None),
                host_is_superhost=str_to_bool(row["host_is_superhost"]),
                host_total_listings_count=to_int(row.get("host_total_listings_count"), default=None),
                host_has_profile_pic=str_to_bool(row["host_has_profile_pic"]),
                host_identity_verified=str_to_bool(row["host_identity_verified"]),
                neighbourhood=clean_value(row.get("neighbourhood")) or "Unknown",
                district=clean_value(row.get("district")) or "Unknown",
                city=clean_value(row.get("city")) or "Unknown",
                latitude=to_float(row.get("latitude")),
                longitude=to_float(row.get("longitude")),
                property_type=clean_value(row.get("property_type")) or "Unknown",
                room_type=clean_value(row.get("room_type")) or "Private room",
                accommodates=to_int(row.get("accommodates"), default=1),
                bedrooms=to_int(row.get("bedrooms"), default=1),
                amenities=clean_value(row.get("amenities")) or "",
                price=to_float(row.get("price"), default=0.0),
                minimum_nights=to_int(row.get("minimum_nights"), default=1),
                maximum_nights=to_int(row.get("maximum_nights"), default=365),
                review_scores_rating=rating_to_five(row.get("review_scores_rating")),
                review_scores_accuracy=subscore_to_five(row.get("review_scores_accuracy")),
                review_scores_cleanliness=subscore_to_five(row.get("review_scores_cleanliness")),
                review_scores_checkin=subscore_to_five(row.get("review_scores_checkin")),
                review_scores_communication=subscore_to_five(row.get("review_scores_communication")),
                review_scores_location=subscore_to_five(row.get("review_scores_location")),
                review_scores_value=subscore_to_five(row.get("review_scores_value")),
                instant_bookable=str_to_bool(row["instant_bookable"]),
            )
            db.add(listing)
            count += 1

    db.commit()
    seed_demo_users(db)
    imported_reviews = seed_historical_reviews(db, os.path.abspath(DEFAULT_REVIEWS_CSV))
    db.close()
    print(f"Seeded {count} listings and {imported_reviews} historical reviews")


if __name__ == "__main__":
    main()
