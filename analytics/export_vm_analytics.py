"""Export the approved city analytics response for the VM API adapter."""

import argparse
import json
from pathlib import Path

import pandas as pd

CURRENCY_BY_CITY = {
    "Bangkok": "THB",
    "Cape Town": "ZAR",
    "Hong Kong": "HKD",
    "Istanbul": "TRY",
    "Mexico City": "MXN",
    "New York": "USD",
    "Paris": "EUR",
    "Rio de Janeiro": "BRL",
    "Rome": "EUR",
    "Sydney": "AUD",
}


def export_summary(listings_path: Path, output_path: Path) -> None:
    columns = ["city", "price", "review_scores_rating"]
    listings = pd.read_csv(listings_path, usecols=columns, encoding="utf-8", encoding_errors="replace")
    listings["price"] = pd.to_numeric(listings["price"], errors="coerce")
    listings["review_scores_rating"] = pd.to_numeric(listings["review_scores_rating"], errors="coerce")
    valid = listings.dropna(subset=["city", "price"])
    valid = valid[valid["price"] > 0]
    if valid.empty:
        raise ValueError("The listings file contains no positive priced rows")

    thresholds = valid.groupby("city")["price"].quantile(0.99)
    valid = valid[valid.apply(lambda row: row["price"] <= thresholds[row["city"]], axis=1)]
    grouped = valid.groupby("city", sort=True)
    items = []
    for city, group in grouped:
        average_price = float(group["price"].mean())
        median_price = float(group["price"].median())
        average_rating = group["review_scores_rating"].mean()
        items.append(
            {
                "city": city,
                "currency": CURRENCY_BY_CITY.get(city, "LOCAL"),
                "listing_count": int(group.shape[0]),
                "average_nightly_price": round(average_price, 2),
                "median_nightly_price": round(median_price, 2),
                "average_to_median_ratio": round(average_price / median_price, 2)
                if median_price > 0
                else None,
                "average_rating": round(float(average_rating), 1)
                if pd.notna(average_rating)
                else None,
            }
        )

    result = {
        "items": items,
        "count": len(items),
        "price_basis": "Local currency for each city",
        "scope": "Positive prices up to each city's observed 99th percentile",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listings", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/analytics-summary.json"))
    arguments = parser.parse_args()
    export_summary(arguments.listings, arguments.output)


if __name__ == "__main__":
    main()
