import base64
import json
import logging
import os

import joblib
import numpy as np
import pandas as pd


logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "model", "airbnb_price_model.joblib"),
)
CURRENCY_BY_CITY = {
    "Bangkok": "THB",
    "Cape Town": "ZAR",
    "Hong Kong": "HKD",
    "Istanbul": "TRY",
    "Mexico City": "MXN",
    "New York": "USD",
    "Paris": "EUR",
    "Rio de Janeiro": "BRL",
    "Rome": "EUR",
    "Sydney": "AUD",
}
BOOLEAN_FIELDS = (
    "instant_bookable",
    "host_is_superhost",
    "host_identity_verified",
)
STRING_FIELDS = ("city", "neighbourhood", "property_type", "room_type")
NUMERIC_BOUNDS = {
    "latitude": (-90, 90),
    "longitude": (-180, 180),
    "accommodates": (1, 16),
    "bedrooms": (0, 50),
    "minimum_nights": (1, 365),
    "review_scores_rating": (20, 100),
    "host_total_listings_count": (0, 10000),
    "amenities_count": (0, 200),
}
OPTIONAL_NUMERIC_FIELDS = {"bedrooms", "review_scores_rating"}
INTEGER_FIELDS = {
    "accommodates",
    "bedrooms",
    "minimum_nights",
    "host_total_listings_count",
    "amenities_count",
}
REQUIRED_FIELDS = (
    set(STRING_FIELDS)
    | set(BOOLEAN_FIELDS)
    | (set(NUMERIC_BOUNDS) - OPTIONAL_NUMERIC_FIELDS)
)
ALLOWED_FIELDS = REQUIRED_FIELDS | OPTIONAL_NUMERIC_FIELDS

_model_bundle = None


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
        },
        "body": json.dumps(body),
    }


def error_response(status_code, code, message, details=None):
    error = {"code": code, "message": message}
    if details:
        error["details"] = details
    return response(status_code, {"error": error})


def load_model():
    global _model_bundle
    if _model_bundle is None:
        _model_bundle = joblib.load(MODEL_PATH)
    return _model_bundle


def parse_body(event):
    if not isinstance(event, dict):
        raise ValueError("Request event must be an object.")
    body = event.get("body")
    if event.get("isBase64Encoded") and isinstance(body, str):
        body = base64.b64decode(body).decode("utf-8")
    if isinstance(body, str):
        body = json.loads(body)
    if not isinstance(body, dict):
        raise ValueError("Request body must be a JSON object.")
    return body


def validate_input(payload, metadata):
    errors = []
    missing = sorted(REQUIRED_FIELDS - set(payload))
    unknown = sorted(set(payload) - ALLOWED_FIELDS)
    if missing:
        errors.append(f"Missing required fields: {', '.join(missing)}")
    if unknown:
        errors.append(f"Unknown fields: {', '.join(unknown)}")

    observed_categories = metadata["observed_categories"]
    for field in STRING_FIELDS:
        value = payload.get(field)
        if field in missing:
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")
            continue
        if value not in observed_categories[field]:
            errors.append(f"{field} is not a supported value")

    city = payload.get("city")
    neighbourhood = payload.get("neighbourhood")
    if (
        isinstance(city, str)
        and isinstance(neighbourhood, str)
        and city in metadata["city_neighbourhoods"]
        and neighbourhood not in metadata["city_neighbourhoods"][city]
    ):
        errors.append("neighbourhood is not valid for the selected city")

    for field in BOOLEAN_FIELDS:
        if field not in payload:
            continue
        if not isinstance(payload[field], bool):
            errors.append(f"{field} must be a boolean")

    for field, (minimum, maximum) in NUMERIC_BOUNDS.items():
        value = payload.get(field)
        if value is None and field in OPTIONAL_NUMERIC_FIELDS:
            continue
        if field in missing:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{field} must be numeric")
            continue
        if not np.isfinite(value) or value < minimum or value > maximum:
            errors.append(f"{field} must be between {minimum} and {maximum}")
        elif field in INTEGER_FIELDS and not float(value).is_integer():
            errors.append(f"{field} must be a whole number")

    if isinstance(city, str) and city in metadata["city_coordinate_ranges"]:
        coordinate_ranges = metadata["city_coordinate_ranges"][city]
        for field in ("latitude", "longitude"):
            value = payload.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            minimum = coordinate_ranges[field]["minimum"]
            maximum = coordinate_ranges[field]["maximum"]
            if value < minimum or value > maximum:
                errors.append(f"{field} is outside the observed range for {city}")

    if errors:
        return None, errors

    transformed = dict(payload)
    for field in OPTIONAL_NUMERIC_FIELDS:
        transformed.setdefault(field, None)
    for field in BOOLEAN_FIELDS:
        transformed[field] = "t" if transformed[field] else "f"
    return transformed, []


def lambda_handler(event, context):
    try:
        payload = parse_body(event)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return error_response(400, "invalid_json", "Request body must be valid JSON.")

    try:
        bundle = load_model()
        model_input, errors = validate_input(payload, bundle["metadata"])
        if errors:
            return error_response(400, "validation_error", "Prediction input is invalid.", errors)

        model = bundle["model"]
        metadata = bundle["metadata"]
        prediction = float(model.predict(pd.DataFrame([model_input]))[0])
        city = model_input["city"]
        maximum = metadata["price_scope"]["city_maximum_supported_price"][city]
        capped_prediction = float(np.clip(prediction, 1, maximum))
        was_capped = not np.isclose(prediction, capped_prediction)

        request_context = event.get("requestContext", {})
        logger.info(
            json.dumps(
                {
                    "event": "price_prediction",
                    "request_id": request_context.get("requestId", "unknown"),
                    "model_version": metadata["model_version"],
                }
            )
        )

        return response(
            200,
            {
                "estimated_nightly_price": round(capped_prediction, 2),
                "currency": CURRENCY_BY_CITY[city],
                "city": city,
                "model_version": metadata["model_version"],
                "prediction_capped": was_capped,
                "supported_market_upper_bound": maximum,
                "disclaimer": "This is a model estimate, not a guaranteed market price.",
            },
        )
    except Exception:
        logger.exception("price_prediction_failed")
        return error_response(500, "internal_error", "The prediction service is temporarily unavailable.")
