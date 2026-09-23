import importlib.util
import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path


HANDLER_PATH = Path(__file__).parents[1] / "src" / "backend" / "history" / "handler.py"
SPEC = importlib.util.spec_from_file_location("history_handler", HANDLER_PATH)
history_handler = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = history_handler
SPEC.loader.exec_module(history_handler)


class FakeHistoryTable:
    def __init__(self):
        self.key_expression = None

    def query(self, **kwargs):
        self.key_expression = kwargs["KeyConditionExpression"]
        return {
            "Items": [
                {
                    "user_id": "authenticated-user",
                    "created_at_prediction_id": "2026-09-23T00:00:00Z#prediction",
                    "predicted_price": Decimal("65.98"),
                }
            ]
        }


class HistoryHandlerTests(unittest.TestCase):
    def setUp(self):
        self.table = FakeHistoryTable()
        history_handler._history_table = self.table

    def test_rejects_request_without_jwt_claims(self):
        response = history_handler.lambda_handler({"requestContext": {}}, None)

        self.assertEqual(response["statusCode"], 401)

    def test_queries_only_authenticated_user(self):
        event = {
            "requestContext": {
                "requestId": "test",
                "authorizer": {"jwt": {"claims": {"sub": "authenticated-user"}}},
            }
        }

        response = history_handler.lambda_handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["items"][0]["predicted_price"], 65.98)
        expression = self.table.key_expression.get_expression()
        self.assertEqual(expression["values"][1], "authenticated-user")


if __name__ == "__main__":
    unittest.main()
