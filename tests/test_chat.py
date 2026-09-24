import importlib.util
import json
import sys
import unittest
from pathlib import Path


HANDLER_PATH = Path(__file__).parents[1] / "src" / "backend" / "chat" / "handler.py"
SPEC = importlib.util.spec_from_file_location("chat_handler", HANDLER_PATH)
chat_handler = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = chat_handler
SPEC.loader.exec_module(chat_handler)


class FakeBedrock:
    def __init__(self, fail=False):
        self.fail = fail
        self.request = None

    def converse(self, **kwargs):
        self.request = kwargs
        if self.fail:
            raise RuntimeError("bedrock unavailable")
        return {
            "output": {"message": {"content": [{"text": "Use the estimator form."}]}},
            "usage": {"inputTokens": 20, "outputTokens": 6},
        }


class ChatHandlerTests(unittest.TestCase):
    def test_returns_bounded_model_reply(self):
        fake = FakeBedrock()
        chat_handler._bedrock = fake

        result = chat_handler.lambda_handler(
            {"body": json.dumps({"message": "How do I estimate a price?", "page": "index.html"})},
            None,
        )
        body = json.loads(result["body"])

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(body["reply"], "Use the estimator form.")
        self.assertEqual(fake.request["modelId"], chat_handler.MODEL_ID)
        self.assertEqual(fake.request["inferenceConfig"]["maxTokens"], 220)

    def test_rejects_empty_message(self):
        result = chat_handler.lambda_handler({"body": '{"message":"  "}'}, None)
        self.assertEqual(result["statusCode"], 400)

    def test_rejects_oversized_message(self):
        result = chat_handler.lambda_handler(
            {"body": json.dumps({"message": "x" * 501})},
            None,
        )
        self.assertEqual(result["statusCode"], 400)

    def test_rejects_unknown_fields(self):
        result = chat_handler.lambda_handler(
            {"body": json.dumps({"message": "hello", "admin": True})},
            None,
        )
        self.assertEqual(result["statusCode"], 400)

    def test_returns_safe_error_when_bedrock_fails(self):
        chat_handler._bedrock = FakeBedrock(fail=True)
        result = chat_handler.lambda_handler(
            {"body": json.dumps({"message": "hello"})},
            None,
        )
        body = json.loads(result["body"])

        self.assertEqual(result["statusCode"], 503)
        self.assertEqual(body["error"]["code"], "assistant_unavailable")
        self.assertNotIn("bedrock", body["error"]["message"].lower())


if __name__ == "__main__":
    unittest.main()
