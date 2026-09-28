import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from botocore.exceptions import ClientError


HANDLER_PATH = Path(__file__).parents[1] / "src" / "backend" / "predict" / "handler.py"
SPEC = importlib.util.spec_from_file_location("prediction_handler", HANDLER_PATH)
prediction_handler = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prediction_handler
SPEC.loader.exec_module(prediction_handler)


class FakeModel:
    def __init__(self, prediction=125.5):
        self.prediction = prediction

    def predict(self, frame):
        return np.array([self.prediction])


class FakeHistoryTable:
    def __init__(self):
        self.items = []

    def put_item(self, **kwargs):
        self.items.append(kwargs["Item"])


class FakeIdempotencyTable:
    def __init__(self):
        self.items = {}

    def put_item(self, **kwargs):
        item = kwargs["Item"]
        key = (item["user_id"], item["idempotency_key"])
        if key in self.items:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "PutItem",
            )
        self.items[key] = item

    def get_item(self, **kwargs):
        key = (kwargs["Key"]["user_id"], kwargs["Key"]["idempotency_key"])
        return {"Item": self.items[key]}

    def update_item(self, **kwargs):
        key = (kwargs["Key"]["user_id"], kwargs["Key"]["idempotency_key"])
        self.items[key]["status"] = "COMPLETED"
        self.items[key]["response_body"] = kwargs["ExpressionAttributeValues"][":response_body"]
        self.items[key]["response_status"] = 200


def model_bundle(prediction=125.5):
    return {
        "model": FakeModel(prediction),
        "metadata": {
            "model_version": "test",
            "observed_categories": {
                "city": ["Paris"],
                "neighbourhood": ["Central"],
                "property_type": ["Entire apartment"],
                "room_type": ["Entire place"],
                "instant_bookable": ["f", "t"],
                "host_is_superhost": ["f", "t"],
                "host_identity_verified": ["f", "t"],
            },
            "city_neighbourhoods": {"Paris": ["Central"]},
            "city_coordinate_ranges": {
                "Paris": {
                    "latitude": {"minimum": 48.8, "maximum": 48.9},
                    "longitude": {"minimum": 2.2, "maximum": 2.5},
                }
            },
            "price_scope": {"city_maximum_supported_price": {"Paris": 500.0}},
        },
    }


def valid_payload():
    return {
        "city": "Paris",
        "neighbourhood": "Central",
        "property_type": "Entire apartment",
        "room_type": "Entire place",
        "instant_bookable": True,
        "host_is_superhost": False,
        "host_identity_verified": True,
        "latitude": 48.86,
        "longitude": 2.35,
        "accommodates": 2,
        "bedrooms": 1,
        "minimum_nights": 2,
        "review_scores_rating": 95,
        "host_total_listings_count": 1,
        "amenities_count": 8,
    }


class PredictionHandlerTests(unittest.TestCase):
    def setUp(self):
        prediction_handler._model_bundle = model_bundle()
        self.history_table = FakeHistoryTable()
        prediction_handler._history_table = self.history_table
        self.idempotency_table = FakeIdempotencyTable()
        prediction_handler._idempotency_table = self.idempotency_table
        prediction_handler.IDEMPOTENCY_TABLE_NAME = "idempotency"

    def test_returns_real_model_response_shape(self):
        event = {"body": json.dumps(valid_payload()), "requestContext": {"requestId": "test"}}

        response = prediction_handler.lambda_handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["estimated_nightly_price"], 125.5)
        self.assertEqual(body["currency"], "EUR")
        self.assertEqual(body["model_version"], "test")
        self.assertFalse(body["prediction_capped"])
        self.assertFalse(body["saved"])
        self.assertEqual(self.history_table.items, [])

    def test_rejects_missing_fields(self):
        payload = valid_payload()
        del payload["city"]

        response = prediction_handler.lambda_handler({"body": json.dumps(payload)}, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(body["error"]["code"], "validation_error")

    def test_rejects_wrong_city_neighbourhood_pair(self):
        payload = valid_payload()
        payload["neighbourhood"] = "Unknown"

        response = prediction_handler.lambda_handler({"body": json.dumps(payload)}, None)

        self.assertEqual(response["statusCode"], 400)

    def test_rejects_malformed_json(self):
        response = prediction_handler.lambda_handler({"body": "{"}, None)

        self.assertEqual(response["statusCode"], 400)

    def test_rejects_coordinates_outside_selected_city(self):
        payload = valid_payload()
        payload["latitude"] = -33.86

        response = prediction_handler.lambda_handler({"body": json.dumps(payload)}, None)

        self.assertEqual(response["statusCode"], 400)

    def test_caps_prediction_to_supported_market(self):
        prediction_handler._model_bundle = model_bundle(prediction=700)
        response = prediction_handler.lambda_handler(
            {"body": json.dumps(valid_payload()), "requestContext": {}},
            None,
        )
        body = json.loads(response["body"])

        self.assertEqual(body["estimated_nightly_price"], 500)
        self.assertTrue(body["prediction_capped"])

    def test_authenticated_prediction_is_saved_for_claimed_user(self):
        event = {
            "body": json.dumps(valid_payload()),
            "requestContext": {
                "requestId": "test",
                "authorizer": {"jwt": {"claims": {"sub": "authenticated-user"}}},
            },
            "headers": {"Idempotency-Key": "test-prediction-1"},
        }

        response = prediction_handler.lambda_handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(body["saved"])
        self.assertEqual(len(self.history_table.items), 1)
        self.assertEqual(self.history_table.items[0]["user_id"], "authenticated-user")

    def test_authenticated_prediction_requires_idempotency_key(self):
        event = {
            "body": json.dumps(valid_payload()),
            "requestContext": {"authorizer": {"jwt": {"claims": {"sub": "authenticated-user"}}}},
        }

        response = prediction_handler.lambda_handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(body["error"]["code"], "missing_idempotency_key")

    def test_authenticated_retry_replays_original_result(self):
        event = {
            "body": json.dumps(valid_payload()),
            "headers": {"idempotency-key": "retryable-prediction"},
            "requestContext": {"authorizer": {"jwt": {"claims": {"sub": "authenticated-user"}}}},
        }

        first = prediction_handler.lambda_handler(event, None)
        second = prediction_handler.lambda_handler(event, None)

        self.assertEqual(first["statusCode"], 200)
        self.assertEqual(second["statusCode"], 200)
        self.assertEqual(json.loads(first["body"])["prediction_id"], json.loads(second["body"])["prediction_id"])
        self.assertEqual(len(self.history_table.items), 1)


if __name__ == "__main__":
    unittest.main()
