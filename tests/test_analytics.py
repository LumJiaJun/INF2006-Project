import importlib.util
import json
import sys
import unittest
from pathlib import Path


HANDLER_PATH = Path(__file__).parents[1] / "src" / "backend" / "analytics" / "handler.py"
SPEC = importlib.util.spec_from_file_location("analytics_handler", HANDLER_PATH)
analytics_handler = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = analytics_handler
SPEC.loader.exec_module(analytics_handler)


class FakeAthena:
    def __init__(self, state="SUCCEEDED"):
        self.state = state
        self.query = None

    def start_query_execution(self, **kwargs):
        self.query = kwargs
        return {"QueryExecutionId": "query-123"}

    def get_query_execution(self, **kwargs):
        return {"QueryExecution": {"Status": {"State": self.state}}}

    def get_query_results(self, **kwargs):
        return {
            "ResultSet": {
                "Rows": [
                    {
                        "Data": [
                            {"VarCharValue": "city"},
                            {"VarCharValue": "listing_count"},
                            {"VarCharValue": "average_nightly_price"},
                            {"VarCharValue": "median_nightly_price"},
                            {"VarCharValue": "average_rating"},
                        ]
                    },
                    {
                        "Data": [
                            {"VarCharValue": "Paris"},
                            {"VarCharValue": "100"},
                            {"VarCharValue": "110.25"},
                            {"VarCharValue": "90.0"},
                            {"VarCharValue": "94.5"},
                        ]
                    },
                ]
            }
        }


class AnalyticsHandlerTests(unittest.TestCase):
    def setUp(self):
        analytics_handler.DATABASE_NAME = "database"
        analytics_handler.TABLE_NAME = "listings"
        analytics_handler.WORKGROUP_NAME = "workgroup"

    def test_returns_typed_city_summary_from_fixed_query(self):
        fake = FakeAthena()
        analytics_handler._athena = fake

        result = analytics_handler.lambda_handler({"requestContext": {"requestId": "test"}}, None)
        body = json.loads(result["body"])

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(body["items"][0]["listing_count"], 100)
        self.assertEqual(body["items"][0]["average_nightly_price"], 110.25)
        self.assertEqual(body["items"][0]["currency"], "EUR")
        self.assertIn("GROUP BY city", fake.query["QueryString"])
        self.assertEqual(fake.query["QueryExecutionContext"]["Database"], "database")

    def test_returns_safe_error_when_query_fails(self):
        analytics_handler._athena = FakeAthena(state="FAILED")

        result = analytics_handler.lambda_handler({}, None)
        body = json.loads(result["body"])

        self.assertEqual(result["statusCode"], 500)
        self.assertEqual(body["error"]["code"], "internal_error")
        self.assertNotIn("Athena", body["error"]["message"])


if __name__ == "__main__":
    unittest.main()
