import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

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


def conditional_failure(operation):
    return ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, operation)


class FakeHistoryTable:
    def __init__(self):
        self.items = []
        self.fail_next_put = False

    def put_item(self, **kwargs):
        if self.fail_next_put:
            self.fail_next_put = False
            raise ClientError({"Error": {"Code": "InternalServerError"}}, "PutItem")
        item = kwargs["Item"]
        if any(existing["created_at_prediction_id"] == item["created_at_prediction_id"] for existing in self.items):
            raise conditional_failure("PutItem")
        self.items.append(item)


class FakeIdempotencyTable:
    def __init__(self):
        self.items = {}
        self.fail_next_complete = False

    def put_item(self, **kwargs):
        item = kwargs["Item"]
        key = (item["user_id"], item["idempotency_key"])
        condition = kwargs.get("ConditionExpression", "")
        if condition == "attribute_not_exists(user_id)" and key in self.items:
            raise conditional_failure("PutItem")
        if condition == "expires_at = :old" and self.items[key]["expires_at"] != kwargs["ExpressionAttributeValues"][":old"]:
            raise conditional_failure("PutItem")
        self.items[key] = dict(item)

    def get_item(self, **kwargs):
        key = (kwargs["Key"]["user_id"], kwargs["Key"]["idempotency_key"])
        return {"Item": self.items[key]} if key in self.items else {}

    def update_item(self, **kwargs):
        key = (kwargs["Key"]["user_id"], kwargs["Key"]["idempotency_key"])
        values = kwargs["ExpressionAttributeValues"]
        item = self.items[key]
        if ":response_body" in values:
            if self.fail_next_complete:
                self.fail_next_complete = False
                raise ClientError({"Error": {"Code": "InternalServerError"}}, "UpdateItem")
            item["status"] = "COMPLETED"
            item["response_body"] = values[":response_body"]
            item["response_status"] = 200
            return
        if item["status"] != "IN_PROGRESS" or ("lease_expires_at" in item and item["lease_expires_at"] != values[":old_lease"]):
            raise conditional_failure("UpdateItem")
        item["lease_expires_at"] = values[":lease"]
        item["created_at"] = values[":created"]
        item["prediction_id"] = values[":prediction"]


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
        saved = self.history_table.items[0]
        self.assertEqual(saved["user_id"], "authenticated-user")
        self.assertEqual(saved["amenities_count"], 8)
        self.assertEqual(saved["host_total_listings_count"], 1)
        self.assertTrue(saved["instant_bookable"])
        self.assertFalse(saved["host_is_superhost"])
        self.assertTrue(saved["host_identity_verified"])
        self.assertEqual(saved["review_scores_rating"], 95)

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

    def authenticated_event(self, key="retry-key", payload=None):
        return {
            "body": json.dumps(payload or valid_payload()),
            "headers": {"Idempotency-Key": key},
            "requestContext": {"authorizer": {"jwt": {"claims": {"sub": "authenticated-user"}}}},
        }

    def call_at(self, event, now):
        with mock.patch.object(prediction_handler.time, "time", return_value=now):
            return prediction_handler.lambda_handler(event, None)

    def test_history_write_failure_is_recoverable_with_same_key(self):
        event = self.authenticated_event()
        self.history_table.fail_next_put = True

        first = self.call_at(event, 1_000)
        blocked = self.call_at(event, 1_010)
        recovered = self.call_at(event, 1_000 + prediction_handler.IDEMPOTENCY_LEASE_SECONDS + 1)

        self.assertEqual(first["statusCode"], 500)
        self.assertEqual(blocked["statusCode"], 409)
        self.assertEqual(json.loads(blocked["body"])["error"]["code"], "request_in_progress")
        self.assertEqual(recovered["statusCode"], 200)
        self.assertTrue(json.loads(recovered["body"])["saved"])
        self.assertEqual(len(self.history_table.items), 1)

    def test_completion_failure_retry_reuses_the_saved_record(self):
        event = self.authenticated_event()
        self.idempotency_table.fail_next_complete = True

        first = self.call_at(event, 1_000)
        retry = self.call_at(event, 1_000 + prediction_handler.IDEMPOTENCY_LEASE_SECONDS + 1)
        replay = self.call_at(event, 1_000 + prediction_handler.IDEMPOTENCY_LEASE_SECONDS + 2)

        self.assertEqual(first["statusCode"], 500)
        self.assertEqual(len(self.history_table.items), 1)
        self.assertEqual(retry["statusCode"], 200)
        self.assertEqual(json.loads(retry["body"])["prediction_id"], self.history_table.items[0]["prediction_id"])
        self.assertEqual(replay["body"], retry["body"])
        self.assertEqual(len(self.history_table.items), 1)

    def test_active_lease_blocks_a_duplicate_request(self):
        event = self.authenticated_event()
        self.idempotency_table.fail_next_complete = True

        self.call_at(event, 1_000)
        duplicate = self.call_at(event, 1_030)

        self.assertEqual(duplicate["statusCode"], 409)
        self.assertEqual(json.loads(duplicate["body"])["error"]["code"], "request_in_progress")

    def test_same_key_with_different_input_is_rejected(self):
        first = self.call_at(self.authenticated_event(), 1_000)
        changed = valid_payload()
        changed["amenities_count"] = 9
        conflict = self.call_at(self.authenticated_event(payload=changed), 1_001)

        self.assertEqual(first["statusCode"], 200)
        self.assertEqual(conflict["statusCode"], 409)
        self.assertEqual(json.loads(conflict["body"])["error"]["code"], "idempotency_conflict")

    def test_expired_record_is_replaced_instead_of_replayed(self):
        event = self.authenticated_event()
        first = self.call_at(event, 1_000)
        after_expiry = 1_000 + prediction_handler.IDEMPOTENCY_RECORD_SECONDS + 1
        second = self.call_at(event, after_expiry)

        self.assertEqual(first["statusCode"], 200)
        self.assertEqual(second["statusCode"], 200)
        stored = self.idempotency_table.items[("authenticated-user", "retry-key")]
        self.assertEqual(stored["expires_at"], after_expiry + prediction_handler.IDEMPOTENCY_RECORD_SECONDS)


if __name__ == "__main__":
    unittest.main()
