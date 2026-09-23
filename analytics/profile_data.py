import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PROFILE_CATEGORIES = ("city", "property_type", "room_type", "neighbourhood")
PRICE_QUANTILES = (0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1)
SOURCE_ENCODING = "utf-8"


def parse_args():
    parser = argparse.ArgumentParser(description="Profile the Airbnb source datasets.")
    parser.add_argument("--listings", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scalar(value):
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def profile_listings(path):
    listings = pd.read_csv(
        path,
        encoding=SOURCE_ENCODING,
        encoding_errors="replace",
        low_memory=False,
    )
    missing_counts = listings.isna().sum()
    unique_counts = listings.nunique(dropna=True)
    price = pd.to_numeric(listings["price"], errors="coerce")

    categories = {}
    for column in PROFILE_CATEGORIES:
        if column not in listings:
            continue
        top_values = listings[column].fillna("<missing>").value_counts().head(20)
        categories[column] = {
            "unique_non_null": int(unique_counts[column]),
            "top_values": {str(key): int(value) for key, value in top_values.items()},
        }

    city_price_statistics = {}
    for city, city_rows in listings.assign(price_numeric=price).groupby("city", dropna=False):
        city_price = city_rows["price_numeric"]
        city_price_statistics[str(city)] = {
            "rows": int(len(city_rows)),
            "non_positive_prices": int((city_price <= 0).sum()),
            "median": scalar(city_price.median()),
            "p95": scalar(city_price.quantile(0.95)),
            "p99": scalar(city_price.quantile(0.99)),
            "maximum": scalar(city_price.max()),
        }

    return {
        "file": path.name,
        "sha256": sha256(path),
        "encoding": SOURCE_ENCODING,
        "encoding_error_handling": "replace",
        "replacement_characters": int(
            listings.select_dtypes(include="object")
            .apply(lambda column: column.str.count("�").sum())
            .sum()
        ),
        "rows": int(len(listings)),
        "columns": listings.columns.tolist(),
        "column_count": int(len(listings.columns)),
        "duplicate_rows": int(listings.duplicated().sum()),
        "duplicate_listing_ids": int(listings["listing_id"].duplicated().sum()),
        "dtypes": {column: str(dtype) for column, dtype in listings.dtypes.items()},
        "missing": {
            column: {
                "count": int(missing_counts[column]),
                "rate": round(float(missing_counts[column] / len(listings)), 6),
            }
            for column in listings.columns
        },
        "unique_non_null": {column: int(unique_counts[column]) for column in listings.columns},
        "price": {
            "non_numeric_or_missing": int(price.isna().sum()),
            "non_positive": int((price <= 0).sum()),
            "mean": scalar(price.mean()),
            "standard_deviation": scalar(price.std()),
            "quantiles": {
                str(quantile): scalar(value)
                for quantile, value in price.quantile(PRICE_QUANTILES).items()
            },
        },
        "categories": categories,
        "city_price_statistics": city_price_statistics,
    }


def profile_reviews(path):
    rows = 0
    columns = None
    minimum_date = None
    maximum_date = None
    listing_ids = set()

    for chunk in pd.read_csv(
        path,
        chunksize=250_000,
        encoding=SOURCE_ENCODING,
        encoding_errors="replace",
        low_memory=False,
    ):
        if columns is None:
            columns = chunk.columns.tolist()
        rows += len(chunk)
        listing_ids.update(chunk["listing_id"].dropna().astype(str).unique())
        dates = pd.to_datetime(chunk["date"], errors="coerce")
        chunk_minimum = dates.min()
        chunk_maximum = dates.max()
        if pd.notna(chunk_minimum):
            minimum_date = chunk_minimum if minimum_date is None else min(minimum_date, chunk_minimum)
        if pd.notna(chunk_maximum):
            maximum_date = chunk_maximum if maximum_date is None else max(maximum_date, chunk_maximum)

    return {
        "file": path.name,
        "sha256": sha256(path),
        "encoding": SOURCE_ENCODING,
        "encoding_error_handling": "replace",
        "rows": int(rows),
        "columns": columns,
        "column_count": len(columns or []),
        "unique_listing_ids": len(listing_ids),
        "minimum_date": minimum_date.date().isoformat() if minimum_date is not None else None,
        "maximum_date": maximum_date.date().isoformat() if maximum_date is not None else None,
        "contains_review_text": bool(
            set(columns or []).intersection({"comments", "comment", "review", "review_text", "text"})
        ),
    }


def main():
    args = parse_args()
    if not args.listings.is_file():
        raise FileNotFoundError(f"Listings dataset not found: {args.listings}")
    if not args.reviews.is_file():
        raise FileNotFoundError(f"Reviews dataset not found: {args.reviews}")

    profile = {
        "listings": profile_listings(args.listings),
        "reviews": profile_reviews(args.reviews),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    print(f"Wrote dataset profile to {args.output}")


if __name__ == "__main__":
    main()
