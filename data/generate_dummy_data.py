"""
Generates synthetic Airbnb-style listings and reviews data.

This is NOT the real Kaggle "Airbnb Listings and Reviews" dataset.
It is dummy/synthetic data that follows the same column names and
data types documented publicly for that dataset, so the application
and ML pipeline can be built and tested before the real dataset is
downloaded and inspected.

Run:
    python generate_dummy_data.py

Outputs:
    data/sample/dummy_listings.csv
    data/sample/dummy_reviews.csv
"""
import csv
import random
import hashlib
import math
from datetime import datetime, timedelta

random.seed(42)

CITIES = ["Singapore", "Bangkok", "Kuala Lumpur", "Jakarta", "Manila"]
CITY_COORDS = {
    # Real approximate city-centre coordinates, so the synthetic data
    # is at least geographically plausible (small jitter added per
    # listing so they don't all sit on one point).
    "Singapore": (1.3521, 103.8198),
    "Bangkok": (13.7563, 100.5018),
    "Kuala Lumpur": (3.1390, 101.6869),
    "Jakarta": (-6.2088, 106.8456),
    "Manila": (14.5995, 120.9842),
}
NEIGHBOURHOODS = {
    "Singapore": ["Bugis", "Tiong Bahru", "Katong", "Jurong East", "Orchard"],
    "Bangkok": ["Sukhumvit", "Silom", "Thonglor", "Chinatown"],
    "Kuala Lumpur": ["Bukit Bintang", "KLCC", "Bangsar"],
    "Jakarta": ["Menteng", "Kemang", "Senayan"],
    "Manila": ["Makati", "BGC", "Malate"],
}
DISTRICTS = ["Central", "East", "West", "North", "South"]
PROPERTY_TYPES = ["Apartment", "Condominium", "House", "Loft", "Serviced apartment"]
ROOM_TYPES = ["Entire home/apt", "Private room", "Shared room"]
RESPONSE_TIMES = ["within an hour", "within a few hours", "within a day", "a few days or more"]
AMENITY_POOL = [
    "Wifi", "Air conditioning", "Kitchen", "Washer", "Free parking",
    "Pool", "Gym", "Elevator", "TV", "Heating", "Iron", "Workspace",
]

N_LISTINGS = 600
N_REVIEWS = 3500


def neighbourhood_offset(name):
    """
    Deterministic small lat/lng offset per neighbourhood name, so
    neighbourhoods within the same city form distinguishable clusters
    on a map instead of all landing on the city centre point. Not real
    geography — just a stable, reproducible spread for demo purposes.
    """
    h = int(hashlib.md5(name.encode()).hexdigest(), 16)
    angle = (h % 360) * (math.pi / 180)
    radius = 0.015 + ((h // 360) % 100) / 100 * 0.035  # ~1.5km to 5km
    return radius * math.cos(angle), radius * math.sin(angle)


def make_listing(listing_id):
    city = random.choice(CITIES)
    neighbourhood = random.choice(NEIGHBOURHOODS[city])
    property_type = random.choice(PROPERTY_TYPES)
    room_type = random.choices(ROOM_TYPES, weights=[0.55, 0.4, 0.05])[0]
    accommodates = random.randint(1, 8)
    bedrooms = max(1, round(accommodates / 2))

    base_price = {
        "Entire home/apt": 120,
        "Private room": 55,
        "Shared room": 25,
    }[room_type]
    price = round(
        base_price
        + bedrooms * 22
        + accommodates * 6
        + random.uniform(-15, 40)
        + (25 if property_type in ("Condominium", "Serviced apartment") else 0),
        2,
    )
    price = max(15.0, price)

    host_since = datetime(2015, 1, 1) + timedelta(days=random.randint(0, 3800))
    is_superhost = random.random() < 0.22
    identity_verified = random.random() < 0.8
    has_profile_pic = random.random() < 0.97

    n_amenities = random.randint(3, len(AMENITY_POOL))
    amenities = random.sample(AMENITY_POOL, n_amenities)

    review_rating = round(random.uniform(3.2, 5.0), 2)

    base_lat, base_lng = CITY_COORDS[city]
    nb_dlat, nb_dlng = neighbourhood_offset(neighbourhood)
    latitude = round(base_lat + nb_dlat + random.uniform(-0.006, 0.006), 6)
    longitude = round(base_lng + nb_dlng + random.uniform(-0.006, 0.006), 6)

    return {
        "listing_id": listing_id,
        "name": f"{room_type} in {neighbourhood}, {city}",
        "host_id": 1000 + (listing_id % 220),
        "host_since": host_since.strftime("%Y-%m-%d"),
        "host_location": city,
        "host_response_time": random.choice(RESPONSE_TIMES),
        "host_response_rate": random.randint(50, 100),
        "host_acceptance_rate": random.randint(50, 100),
        "host_is_superhost": is_superhost,
        "host_total_listings_count": random.randint(1, 15),
        "host_has_profile_pic": has_profile_pic,
        "host_identity_verified": identity_verified,
        "neighbourhood": neighbourhood,
        "district": random.choice(DISTRICTS),
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "property_type": property_type,
        "room_type": room_type,
        "accommodates": accommodates,
        "bedrooms": bedrooms,
        "amenities": "|".join(amenities),
        "price": price,
        "minimum_nights": random.choice([1, 1, 2, 2, 3, 7]),
        "maximum_nights": random.choice([30, 60, 90, 365, 1125]),
        "review_scores_rating": review_rating,
        "review_scores_accuracy": round(min(5.0, review_rating + random.uniform(-0.3, 0.2)), 2),
        "review_scores_cleanliness": round(min(5.0, review_rating + random.uniform(-0.4, 0.2)), 2),
        "review_scores_checkin": round(min(5.0, review_rating + random.uniform(-0.2, 0.3)), 2),
        "review_scores_communication": round(min(5.0, review_rating + random.uniform(-0.2, 0.3)), 2),
        "review_scores_location": round(min(5.0, review_rating + random.uniform(-0.3, 0.3)), 2),
        "review_scores_value": round(min(5.0, review_rating + random.uniform(-0.4, 0.1)), 2),
        "instant_bookable": random.random() < 0.5,
    }


def make_review(review_id, listing_id):
    start = datetime(2016, 1, 1)
    date = start + timedelta(days=random.randint(0, 3800))
    return {
        "listing_id": listing_id,
        "review_id": review_id,
        "date": date.strftime("%Y-%m-%d"),
        "reviewer_id": random.randint(5000, 5000 + N_REVIEWS * 2),
    }


def main():
    listings = [make_listing(lid) for lid in range(1, N_LISTINGS + 1)]

    with open("sample/dummy_listings.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(listings[0].keys()))
        writer.writeheader()
        writer.writerows(listings)

    reviews = []
    review_id = 1
    for _ in range(N_REVIEWS):
        listing_id = random.randint(1, N_LISTINGS)
        reviews.append(make_review(review_id, listing_id))
        review_id += 1

    with open("sample/dummy_reviews.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(reviews[0].keys()))
        writer.writeheader()
        writer.writerows(reviews)

    print(f"Wrote {len(listings)} listings and {len(reviews)} reviews.")


if __name__ == "__main__":
    main()
