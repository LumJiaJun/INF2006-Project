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

from .database import Base, engine, SessionLocal
from . import models, auth

DEFAULT_CSV = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "sample", "dummy_listings.csv"
)

DEMO_PASSWORD = "Demo1234!"


def str_to_bool(value: str) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


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
        db.close()
        return

    count = 0
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            listing = models.Listing(
                listing_id=int(row["listing_id"]),
                name=row["name"],
                host_id=int(row["host_id"]),
                host_since=row["host_since"],
                host_location=row["host_location"],
                host_response_time=row["host_response_time"],
                host_response_rate=int(row["host_response_rate"]),
                host_acceptance_rate=int(row["host_acceptance_rate"]),
                host_is_superhost=str_to_bool(row["host_is_superhost"]),
                host_total_listings_count=int(row["host_total_listings_count"]),
                host_has_profile_pic=str_to_bool(row["host_has_profile_pic"]),
                host_identity_verified=str_to_bool(row["host_identity_verified"]),
                neighbourhood=row["neighbourhood"],
                district=row["district"],
                city=row["city"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                property_type=row["property_type"],
                room_type=row["room_type"],
                accommodates=int(row["accommodates"]),
                bedrooms=int(row["bedrooms"]),
                amenities=row["amenities"],
                price=float(row["price"]),
                minimum_nights=int(row["minimum_nights"]),
                maximum_nights=int(row["maximum_nights"]),
                review_scores_rating=float(row["review_scores_rating"]),
                review_scores_accuracy=float(row["review_scores_accuracy"]),
                review_scores_cleanliness=float(row["review_scores_cleanliness"]),
                review_scores_checkin=float(row["review_scores_checkin"]),
                review_scores_communication=float(row["review_scores_communication"]),
                review_scores_location=float(row["review_scores_location"]),
                review_scores_value=float(row["review_scores_value"]),
                instant_bookable=str_to_bool(row["instant_bookable"]),
            )
            db.add(listing)
            count += 1

    db.commit()
    seed_demo_users(db)
    db.close()
    print(f"Seeded {count} listings from {csv_path}")


if __name__ == "__main__":
    main()
