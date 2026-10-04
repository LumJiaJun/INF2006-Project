import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


class SubmissionDataConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_json("analytics/artifacts/data_profile.json")
        cls.evaluation = load_json("analytics/artifacts/model_evaluation.json")
        cls.frontend_options = load_json("src/frontend/model-options.json")

    def test_profile_and_evaluation_reference_the_same_source_hash(self):
        profile_hash = self.profile["listings"]["sha256"]
        evaluation_hash = self.evaluation["dataset"]["sha256"]
        self.assertEqual(profile_hash, evaluation_hash)
        self.assertEqual(len(profile_hash), 64)
        self.assertIn(profile_hash, (ROOT / "data/README.md").read_text(encoding="utf-8"))

    def test_selected_model_has_the_best_declared_selection_metric(self):
        evaluations = self.evaluation["evaluations"]
        scores = {
            name: result["median_city_normalized_mae"]
            for name, result in evaluations.items()
        }
        self.assertEqual(self.evaluation["selection_metric"], "median_city_normalized_mae")
        self.assertEqual(self.evaluation["selected_model"], min(scores, key=scores.get))

    def test_frontend_options_match_evaluated_model_scope(self):
        evaluation = self.evaluation
        cities = {city["name"]: city for city in self.frontend_options["cities"]}
        self.assertEqual(self.frontend_options["model_version"], evaluation["model_version"])
        self.assertEqual(set(cities), set(evaluation["city_neighbourhoods"]))
        self.assertEqual(
            self.frontend_options["property_types"],
            evaluation["observed_categories"]["property_type"],
        )
        self.assertEqual(
            self.frontend_options["room_types"],
            evaluation["observed_categories"]["room_type"],
        )
        for name, city in cities.items():
            self.assertEqual(city["neighbourhoods"], evaluation["city_neighbourhoods"][name])
            self.assertEqual(city["coordinate_range"], evaluation["city_coordinate_ranges"][name])
            self.assertEqual(
                city["supported_market_upper_bound"],
                evaluation["price_scope"]["city_maximum_supported_price"][name],
            )

    def test_synthetic_sample_is_deterministic_and_balanced_by_city(self):
        committed = ROOT / "data/sample/listings_synthetic.csv"
        with tempfile.TemporaryDirectory() as temporary_directory:
            generated = Path(temporary_directory) / "listings_synthetic.csv"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "analytics/generate_sample_data.py"),
                    "--output",
                    str(generated),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                hashlib.sha256(generated.read_bytes()).hexdigest(),
                hashlib.sha256(committed.read_bytes()).hexdigest(),
            )
        with committed.open(encoding="utf-8", newline="") as sample_file:
            rows = list(csv.DictReader(sample_file))
        city_counts = {}
        for row in rows:
            city_counts[row["city"]] = city_counts.get(row["city"], 0) + 1
        self.assertEqual(len(rows), 500)
        self.assertEqual(set(city_counts.values()), {50})

    def test_data_dictionary_covers_every_model_input_and_derived_feature(self):
        dictionary = (ROOT / "data/DATA_DICTIONARY.md").read_text(encoding="utf-8")
        source_features = set(self.evaluation["features"]["categorical"])
        source_features.update(self.evaluation["features"]["numeric"])
        source_features.remove("amenities_count")
        for feature in source_features:
            self.assertIn(f"`{feature}`", dictionary)
        self.assertIn("`amenities_count`", dictionary)
        self.assertIn("derived", dictionary.lower())


if __name__ == "__main__":
    unittest.main()
