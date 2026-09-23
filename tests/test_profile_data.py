import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ANALYTICS_PATH = Path(__file__).parents[1] / "analytics"
sys.path.insert(0, str(ANALYTICS_PATH))

import profile_data


class DataProfileTests(unittest.TestCase):
    def test_profiles_listing_quality_and_city_prices(self):
        listings = pd.DataFrame(
            [
                {
                    "listing_id": 1,
                    "city": "Test City",
                    "property_type": "Apartment",
                    "room_type": "Entire place",
                    "neighbourhood": "Central",
                    "price": 100,
                },
                {
                    "listing_id": 2,
                    "city": "Test City",
                    "property_type": "Apartment",
                    "room_type": "Private room",
                    "neighbourhood": "Central",
                    "price": 0,
                },
            ]
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "listings.csv"
            listings.to_csv(path, index=False)
            result = profile_data.profile_listings(path)

        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["duplicate_listing_ids"], 0)
        self.assertEqual(result["price"]["non_positive"], 1)
        self.assertEqual(result["city_price_statistics"]["Test City"]["median"], 50.0)

    def test_confirms_reviews_have_no_text(self):
        reviews = pd.DataFrame(
            [
                {
                    "listing_id": 1,
                    "review_id": 10,
                    "date": "2021-01-01",
                    "reviewer_id": 100,
                }
            ]
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reviews.csv"
            reviews.to_csv(path, index=False)
            result = profile_data.profile_reviews(path)

        self.assertEqual(result["rows"], 1)
        self.assertFalse(result["contains_review_text"])
        self.assertEqual(result["minimum_date"], "2021-01-01")


if __name__ == "__main__":
    unittest.main()
