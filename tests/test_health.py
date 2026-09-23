import json
import sys
import unittest
from pathlib import Path


HEALTH_FUNCTION_PATH = Path(__file__).parents[1] / "src" / "backend" / "health"
sys.path.insert(0, str(HEALTH_FUNCTION_PATH))

import handler


class LambdaContext:
    aws_request_id = "local-test-request"


class HealthHandlerTests(unittest.TestCase):
    def test_returns_healthy_response(self):
        response = handler.lambda_handler({}, LambdaContext())
        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["content-type"], "application/json")
        self.assertEqual(response["headers"]["cache-control"], "no-store")
        self.assertEqual(body["service"], "airbnb-market-intelligence-api")
        self.assertEqual(body["status"], "healthy")
        self.assertIn("timestamp", body)

    def test_accepts_api_gateway_request_context(self):
        event = {"requestContext": {"requestId": "api-gateway-request"}}

        response = handler.lambda_handler(event, LambdaContext())

        self.assertEqual(response["statusCode"], 200)


if __name__ == "__main__":
    unittest.main()
