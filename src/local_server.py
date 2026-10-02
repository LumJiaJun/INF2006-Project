import argparse
import json
import sys
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import joblib
import pandas as pd


ROOT = Path(__file__).parents[1]
FRONTEND = ROOT / "src" / "frontend"
SAMPLE_DATA = ROOT / "data" / "sample" / "listings_synthetic.csv"
LOCAL_OUTPUT = ROOT / "tmp" / "local-development"
LOCAL_MODEL = LOCAL_OUTPUT / "sample-model.joblib"
LOCAL_METRICS = LOCAL_OUTPUT / "sample-metrics.json"

sys.path.insert(0, str(ROOT))

from analytics.train_model import train_and_export
from src.backend.predict import handler as prediction_handler


def parse_args():
    parser = argparse.ArgumentParser(description="Run the frontend and representative APIs locally.")
    parser.add_argument("--host", choices=("127.0.0.1", "localhost"), default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def ensure_model():
    source_is_newer = not LOCAL_MODEL.exists() or SAMPLE_DATA.stat().st_mtime > LOCAL_MODEL.stat().st_mtime
    if source_is_newer:
        print("Preparing the deterministic local sample model...")
        train_and_export(SAMPLE_DATA, LOCAL_MODEL, LOCAL_METRICS)
    return joblib.load(LOCAL_MODEL)


def local_analytics():
    frame = pd.read_csv(SAMPLE_DATA)
    frame["host_is_superhost"] = frame["host_is_superhost"].eq("t")
    items = []
    currencies = prediction_handler.CURRENCY_BY_CITY
    for city, rows in frame.groupby("city", sort=True):
        threshold = rows["price"].quantile(0.99)
        rows = rows.loc[rows["price"] <= threshold]
        superhost_average = rows.loc[rows["host_is_superhost"], "price"].mean()
        non_superhost_average = rows.loc[~rows["host_is_superhost"], "price"].mean()
        average_price = rows["price"].mean()
        median_price = rows["price"].median()
        items.append(
            {
                "city": city,
                "currency": currencies[city],
                "listing_count": int(len(rows)),
                "average_nightly_price": round(float(average_price), 2),
                "median_nightly_price": round(float(median_price), 2),
                "average_to_median_ratio": round(float(average_price / median_price), 2),
                "average_rating": round(float(rows["review_scores_rating"].mean()), 1),
                "capacity_price_correlation": round(float(rows["price"].corr(rows["accommodates"])), 3),
                "superhost_average_nightly_price": round(float(superhost_average), 2),
                "non_superhost_average_nightly_price": round(float(non_superhost_average), 2),
                "superhost_price_difference_percent": round(
                    float((superhost_average - non_superhost_average) / non_superhost_average * 100),
                    1,
                ),
            }
        )
    return {
        "items": items,
        "count": len(items),
        "price_basis": "Synthetic local data in each city's local currency",
        "scope": "Local development sample only",
        "diagnostic_scope": "Cross-sectional associations only; they do not establish causation.",
    }


def local_model_options(model_bundle):
    metadata = model_bundle["metadata"]
    observed = metadata["observed_categories"]
    bounds = metadata["price_scope"]["city_maximum_supported_price"]
    coordinates = metadata["city_coordinate_ranges"]
    return {
        "model_version": metadata["model_version"],
        "cities": [
            {
                "name": city,
                "neighbourhoods": metadata["city_neighbourhoods"][city],
                "coordinate_range": coordinates[city],
                "supported_market_upper_bound": bounds[city],
            }
            for city in sorted(metadata["city_neighbourhoods"])
        ],
        "property_types": observed["property_type"],
        "room_types": observed["room_type"],
    }


class LocalRequestHandler(SimpleHTTPRequestHandler):
    server_version = "INF2006Local/1.0"

    def send_json(self, status, body):
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.send_header("cache-control", "no-store")
        self.send_header("x-content-type-options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def send_script(self, content):
        encoded = content.encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/javascript; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/config.js":
            self.send_script(
                'window.APP_CONFIG = Object.freeze({ apiBaseUrl: "/api", localMode: true });'
            )
            return
        if path == "/auth-config.js":
            self.send_script("window.AUTH_CONFIG = null;")
            return
        if path == "/model-options.json":
            self.send_json(200, self.server.model_options)
            return
        if path == "/api/health":
            self.send_json(200, {"status": "healthy", "service": "local-development"})
            return
        if path == "/api/analytics":
            self.send_json(200, self.server.analytics)
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/predict":
            self.send_json(404, {"error": {"code": "not_found", "message": "Route not found."}})
            return
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > 64_000:
                raise ValueError("Request body size is invalid.")
            body = self.rfile.read(length).decode("utf-8")
            result = prediction_handler.lambda_handler(
                {"body": body, "requestContext": {"requestId": "local-development"}},
                None,
            )
            self.send_json(int(result["statusCode"]), json.loads(result["body"]))
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
            self.send_json(400, {"error": {"code": "validation_error", "message": "Invalid request."}})
        except Exception:
            self.send_json(500, {"error": {"code": "internal_error", "message": "Local prediction failed."}})

    def log_message(self, message_format, *args):
        print(f"{self.client_address[0]} - {message_format % args}")


def create_server(host="127.0.0.1", port=8000, model_bundle=None):
    model_bundle = model_bundle or ensure_model()
    prediction_handler._model_bundle = model_bundle
    handler = partial(LocalRequestHandler, directory=str(FRONTEND))
    server = ThreadingHTTPServer((host, port), handler)
    server.analytics = local_analytics()
    server.model_options = local_model_options(model_bundle)
    return server


def main():
    args = parse_args()
    server = create_server(args.host, args.port)
    address = f"http://{args.host}:{server.server_port}"
    print(f"Local application: {address}")
    print("Local mode uses synthetic data. Cognito, history, Bedrock, and AWS controls require cloud testing.")
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local application.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
