import argparse
import csv
import hashlib
from pathlib import Path


RANDOM_SEED = 2006
CITIES = {
    "Bangkok": (13.7563, 100.5018, 1800),
    "Cape Town": (-33.9249, 18.4241, 900),
    "Hong Kong": (22.3193, 114.1694, 650),
    "Istanbul": (41.0082, 28.9784, 1400),
    "Mexico City": (19.4326, -99.1332, 1100),
    "New York": (40.7128, -74.0060, 190),
    "Paris": (48.8566, 2.3522, 130),
    "Rio de Janeiro": (-22.9068, -43.1729, 700),
    "Rome": (41.9028, 12.4964, 120),
    "Sydney": (-33.8688, 151.2093, 210),
}
PROPERTY_TYPES = ("Entire apartment", "House", "Guest suite")
ROOM_TYPES = ("Entire place", "Private room")
FIELDNAMES = (
    "city",
    "neighbourhood",
    "property_type",
    "room_type",
    "instant_bookable",
    "host_is_superhost",
    "host_identity_verified",
    "latitude",
    "longitude",
    "accommodates",
    "bedrooms",
    "minimum_nights",
    "review_scores_rating",
    "host_total_listings_count",
    "amenities",
    "price",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic listings for offline checks.")
    parser.add_argument("--output", type=Path, default=Path("data/sample/listings_synthetic.csv"))
    parser.add_argument("--rows-per-city", type=int, default=50)
    return parser.parse_args()


def generated_rows(rows_per_city):
    if rows_per_city < 10:
        raise ValueError("rows-per-city must be at least 10")
    for city, (latitude, longitude, base_price) in CITIES.items():
        for index in range(rows_per_city):
            accommodates = 1 + index % 6
            bedrooms = max(1, (accommodates + 1) // 2)
            amenities_count = 4 + index % 14
            entire_place = index % 3 != 0
            superhost = index % 4 == 0
            rating = 76 + index % 24
            price_multiplier = (
                0.55
                + accommodates * 0.12
                + amenities_count * 0.012
                + (0.18 if entire_place else 0)
                + (0.06 if superhost else 0)
                + deterministic_offset(city, index, "price", 0.06)
            )
            amenities = [f"Sample amenity {number}" for number in range(1, amenities_count + 1)]
            yield {
                "city": city,
                "neighbourhood": f"Synthetic District {index % 5 + 1}",
                "property_type": PROPERTY_TYPES[index % len(PROPERTY_TYPES)],
                "room_type": "Entire place" if entire_place else "Private room",
                "instant_bookable": "t" if index % 2 == 0 else "f",
                "host_is_superhost": "t" if superhost else "f",
                "host_identity_verified": "t" if index % 5 != 0 else "f",
                "latitude": round(latitude + deterministic_offset(city, index, "latitude", 0.04), 6),
                "longitude": round(longitude + deterministic_offset(city, index, "longitude", 0.04), 6),
                "accommodates": accommodates,
                "bedrooms": bedrooms,
                "minimum_nights": 1 + index % 7,
                "review_scores_rating": rating,
                "host_total_listings_count": 1 + index % 8,
                "amenities": str(amenities).replace("'", '"'),
                "price": round(max(base_price * price_multiplier, 1), 2),
            }


def deterministic_offset(city, index, field, limit):
    value = f"{RANDOM_SEED}:{city}:{index}:{field}".encode("utf-8")
    integer = int.from_bytes(hashlib.sha256(value).digest()[:8], "big")
    normalized = integer / ((1 << 64) - 1)
    return (normalized * 2 - 1) * limit


def main():
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = list(generated_rows(args.rows_per_city))
    with args.output.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} deterministic synthetic rows to {args.output}")


if __name__ == "__main__":
    main()
