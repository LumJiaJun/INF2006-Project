import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


ANALYTICS_PATH = Path(__file__).parents[1] / "analytics"
sys.path.insert(0, str(ANALYTICS_PATH))

import train_model


class ModelTrainingTests(unittest.TestCase):
    def test_cleaning_excludes_invalid_rows_and_caps_minimum_nights(self):
        valid_row = {
            "city": "Paris",
            "neighbourhood": "Central",
            "property_type": "Apartment",
            "room_type": "Entire place",
            "instant_bookable": "t",
            "host_is_superhost": "f",
            "host_identity_verified": "t",
            "latitude": 48.8,
            "longitude": 2.3,
            "accommodates": 2,
            "bedrooms": 1,
            "minimum_nights": 9999,
            "review_scores_rating": 95,
            "host_total_listings_count": 1,
            "amenities": '["Wifi", "Kitchen"]',
            "price": 100,
        }
        invalid_price = {**valid_row, "price": 0}
        invalid_capacity = {**valid_row, "accommodates": 0}

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "listings.csv"
            pd.DataFrame([valid_row, invalid_price, invalid_capacity]).to_csv(path, index=False)
            frame, cleaning = train_model.load_training_data(path)

        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["minimum_nights"], 365)
        self.assertEqual(frame.iloc[0]["amenities_count"], 2)
        self.assertEqual(cleaning["excluded_rows"], 2)

    def test_metric_values_are_exact_for_perfect_predictions(self):
        actual = pd.Series([100.0, 200.0, 300.0])
        result = train_model.metric_values(actual, actual)

        self.assertEqual(result["mae"], 0)
        self.assertEqual(result["rmse"], 0)
        self.assertEqual(result["r2"], 1)

    def test_price_scope_uses_training_thresholds(self):
        train_features = pd.DataFrame({"city": ["Paris"] * 4})
        test_features = pd.DataFrame({"city": ["Paris", "Paris"]})
        train_target = pd.Series([50.0, 60.0, 70.0, 1000.0])
        test_target = pd.Series([80.0, 2000.0])

        (
            scoped_train_features,
            scoped_test_features,
            scoped_train_target,
            scoped_test_target,
            scope,
        ) = train_model.apply_price_scope(
            train_features,
            test_features,
            train_target,
            test_target,
        )

        self.assertEqual(len(scoped_train_features), 3)
        self.assertEqual(len(scoped_test_features), 1)
        self.assertEqual(scoped_train_target.max(), 70)
        self.assertEqual(scoped_test_target.max(), 80)
        self.assertEqual(scope["threshold_source"], "training partition only")


if __name__ == "__main__":
    unittest.main()
