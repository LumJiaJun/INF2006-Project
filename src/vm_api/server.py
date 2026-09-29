"""Small VM HTTP adapter for the frontend's local API contract."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

HOST = os.environ.get("VM_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("VM_API_PORT", "8000"))
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANALYTICS_JSON_PATH = os.environ.get(
    "ANALYTICS_JSON_PATH",
    str(PROJECT_ROOT / "data" / "analytics-summary.json"),
)
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    str(PROJECT_ROOT / "analytics" / "artifacts" / "airbnb_price_model.joblib"),
)


def write_json(handler, status_code, body):
    payload = json.dumps(body).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("content-type", "application/json; charset=utf-8")
    handler.send_header("cache-control", "no-store")
    handler.send_header("content-length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def error_body(code, message):
    return {"error": {"code": code, "message": message}}


def load_analytics():
    if not ANALYTICS_JSON_PATH:
        return None
    path = Path(ANALYTICS_JSON_PATH)
    if not path.is_file():
        raise FileNotFoundError(f"Analytics file does not exist: {path}")
    with path.open("r", encoding="utf-8") as analytics_file:
        result = json.load(analytics_file)
    if not isinstance(result, dict) or not isinstance(result.get("items"), list):
        raise ValueError("Analytics file must contain an object with an items array")
    return result


def run_prediction(payload):
    os.environ["MODEL_PATH"] = MODEL_PATH
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from src.backend.predict import handler as prediction_handler

    event = {
        "body": json.dumps(payload),
        "headers": {},
        "requestContext": {},
    }
    return prediction_handler.lambda_handler(event, None)


class VmApiHandler(BaseHTTPRequestHandler):
    server_version = "INF2006VmApi/0.1"

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == "/health":
            write_json(
                self,
                200,
                {
                    "service": "airbnb-market-intelligence-api",
                    "status": "healthy",
                },
            )
            return
        if route == "/analytics":
            try:
                analytics = load_analytics()
            except (OSError, ValueError, json.JSONDecodeError) as error:
                print(f"analytics_load_failed: {error}")
                analytics = None
            if analytics is None:
                write_json(
                    self,
                    503,
                    error_body(
                        "analytics_unavailable",
                        "Market analytics data has not been configured on this VM.",
                    ),
                )
                return
            write_json(self, 200, analytics)
            return
        write_json(self, 404, error_body("not_found", "The requested route was not found."))

    def do_POST(self):
        route = urlsplit(self.path).path
        if route == "/predict":
            if not MODEL_PATH or not Path(MODEL_PATH).is_file():
                write_json(
                    self,
                    503,
                    error_body(
                        "model_unavailable",
                        "The evaluated model artifact has not been configured on this VM.",
                    ),
                )
                return
            try:
                content_length = int(self.headers.get("content-length", "0"))
                payload = json.loads(self.rfile.read(content_length))
                result = run_prediction(payload)
                response_body = json.loads(result["body"])
                write_json(self, result["statusCode"], response_body)
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                write_json(self, 400, error_body("invalid_json", str(error)))
            except Exception as error:
                print(f"prediction_failed: {error!r}", flush=True)
                write_json(
                    self,
                    500,
                    error_body("internal_error", "The prediction service is temporarily unavailable."),
                )
            return
        write_json(self, 404, error_body("not_found", "The requested route was not found."))


def main():
    server = ThreadingHTTPServer((HOST, PORT), VmApiHandler)
    print(f"INF2006 VM API listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
