import base64
import hashlib
import json
import logging
import os
import time
from datetime import UTC, datetime
from decimal import Decimal

import boto3
import joblib
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel(logging.INFO)

MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "model", "airbnb_price_model.joblib"),
)
HISTORY_TABLE_NAME = os.environ.get("HISTORY_TABLE_NAME")
IDEMPOTENCY_TABLE_NAME = os.environ.get("IDEMPOTENCY_TABLE_NAME")
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
# A request that stalls mid-way can be taken over by a retry once its lease expires.
IDEMPOTENCY_LEASE_SECONDS = 60
IDEMPOTENCY_RECORD_SECONDS = 86400

_model_bundle = None
_history_table = None
_idempotency_table = None


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
    # Warm Lambda containers can reuse the model, while durable state stays in AWS services.
    if _model_bundle is None:
        _model_bundle = joblib.load(MODEL_PATH)
    return _model_bundle


def history_table():
    global _history_table
    if _history_table is None:
        if not HISTORY_TABLE_NAME:
            raise RuntimeError("HISTORY_TABLE_NAME is not configured")
        _history_table = boto3.resource("dynamodb").Table(HISTORY_TABLE_NAME)
    return _history_table


def idempotency_table():
    global _idempotency_table
    if _idempotency_table is None:
        if not IDEMPOTENCY_TABLE_NAME:
            raise RuntimeError("IDEMPOTENCY_TABLE_NAME is not configured")
        _idempotency_table = boto3.resource("dynamodb").Table(IDEMPOTENCY_TABLE_NAME)
    return _idempotency_table


def request_header(event, name):
    headers = event.get("headers", {}) if isinstance(event, dict) else {}
    return next((value for key, value in headers.items() if key.lower() == name.lower()), None)


def idempotency_key(event):
    value = request_header(event, "Idempotency-Key")
    if not isinstance(value, str) or not value or len(value) > 128:
        return None
    if not all(character.isalnum() or character in "._-~" for character in value):
        return None
    return value


def request_fingerprint(payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def deterministic_prediction_id(user_id, key):
    # The same user and key always map to the same history record, so a retry cannot duplicate it.
    return hashlib.sha256(f"{user_id}{key}".encode("utf-8")).hexdigest()[:32]


def stored_response(existing):
    return {
        "statusCode": int(existing.get("response_status", 200)),
        "headers": {"content-type": "application/json", "cache-control": "no-store"},
        "body": existing["response_body"],
    }


def in_progress_response():
    return error_response(409, "request_in_progress", "This prediction request is still being processed. Retry shortly.")


def claim_idempotency(user_id, key, fingerprint):
    """Return (early_response, claim). A claim carries the stable identity of the history record."""
    now = int(time.time())
    claim = {
        "created_at": datetime.now(UTC).isoformat(),
        "prediction_id": deterministic_prediction_id(user_id, key),
    }
    record = {
        "user_id": user_id,
        "idempotency_key": key,
        "request_fingerprint": fingerprint,
        "status": "IN_PROGRESS",
        "created_at": claim["created_at"],
        "prediction_id": claim["prediction_id"],
        "lease_expires_at": now + IDEMPOTENCY_LEASE_SECONDS,
        "expires_at": now + IDEMPOTENCY_RECORD_SECONDS,
    }
    try:
        idempotency_table().put_item(Item=record, ConditionExpression="attribute_not_exists(user_id)")
        return None, claim
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
            raise

    existing = idempotency_table().get_item(
        Key={"user_id": user_id, "idempotency_key": key},
        ConsistentRead=True,
    ).get("Item")
    if not existing:
        # The record expired between the two calls; the caller can simply retry.
        return in_progress_response(), None

    if int(existing.get("expires_at", 0)) <= now:
        # A retained record past its expiry is treated as absent and replaced atomically.
        try:
            idempotency_table().put_item(
                Item=record,
                ConditionExpression="expires_at = :old",
                ExpressionAttributeValues={":old": existing["expires_at"]},
            )
            return None, claim
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
                raise
            return in_progress_response(), None

    if existing.get("request_fingerprint") != fingerprint:
        return error_response(409, "idempotency_conflict", "This idempotency key was used for another request."), None
    if existing.get("status") == "COMPLETED" and existing.get("response_body"):
        return stored_response(existing), None
    if int(existing.get("lease_expires_at", 0)) > now:
        return in_progress_response(), None

    # The earlier attempt stalled. Take over its lease while keeping its record identity.
    claim = {
        "created_at": existing.get("created_at") or claim["created_at"],
        "prediction_id": existing.get("prediction_id") or claim["prediction_id"],
    }
    try:
        idempotency_table().update_item(
            Key={"user_id": user_id, "idempotency_key": key},
            UpdateExpression="SET lease_expires_at = :lease, created_at = :created, prediction_id = :prediction",
            ConditionExpression="#status = :in_progress AND (attribute_not_exists(lease_expires_at) OR lease_expires_at = :old_lease)",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":lease": now + IDEMPOTENCY_LEASE_SECONDS,
                ":created": claim["created_at"],
                ":prediction": claim["prediction_id"],
                ":in_progress": "IN_PROGRESS",
                ":old_lease": existing.get("lease_expires_at", 0),
            },
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
            raise
        return in_progress_response(), None
    return None, claim


def complete_idempotency(user_id, key, result):
    idempotency_table().update_item(
        Key={"user_id": user_id, "idempotency_key": key},
        UpdateExpression="SET #status = :status, response_status = :response_status, response_body = :response_body",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":status": "COMPLETED",
            ":response_status": 200,
            ":response_body": json.dumps(result),
        },
    )


def authenticated_user_id(event):
    # API Gateway supplies these claims only after the JWT authorizer verifies the token.
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
        .get("sub")
    )


def persist_prediction(user_id, model_input, result, claim):
    # Coordinates are deliberately excluded from history because they are not needed later.
    prediction_id = claim["prediction_id"]
    created_at = claim["created_at"]
    item = {
        "user_id": user_id,
        "created_at_prediction_id": f"{created_at}#{prediction_id}",
        "prediction_id": prediction_id,
        "created_at": created_at,
        "city": model_input["city"],
        "neighbourhood": model_input["neighbourhood"],
        "property_type": model_input["property_type"],
        "room_type": model_input["room_type"],
        "accommodates": Decimal(str(model_input["accommodates"])),
        "minimum_nights": Decimal(str(model_input["minimum_nights"])),
        "amenities_count": Decimal(str(model_input["amenities_count"])),
        "host_total_listings_count": Decimal(str(model_input["host_total_listings_count"])),
        "instant_bookable": model_input["instant_bookable"] == "t",
        "host_is_superhost": model_input["host_is_superhost"] == "t",
        "host_identity_verified": model_input["host_identity_verified"] == "t",
        "predicted_price": Decimal(str(result["estimated_nightly_price"])),
        "currency": result["currency"],
        "model_version": result["model_version"],
    }
    if model_input.get("bedrooms") is not None:
        item["bedrooms"] = Decimal(str(model_input["bedrooms"]))
    if model_input.get("review_scores_rating") is not None:
        item["review_scores_rating"] = Decimal(str(model_input["review_scores_rating"]))

    try:
        history_table().put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(created_at_prediction_id)",
        )
    except ClientError as error:
        # An earlier attempt with the same key already saved this exact record.
        if error.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
            raise
    return prediction_id


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

        result = {
            "estimated_nightly_price": round(capped_prediction, 2),
            "currency": CURRENCY_BY_CITY[city],
            "city": city,
            "model_version": metadata["model_version"],
            "prediction_capped": was_capped,
            "supported_market_upper_bound": maximum,
            "disclaimer": "This is a model estimate, not a guaranteed market price.",
            "saved": False,
        }
        user_id = authenticated_user_id(event)
        if user_id:
            key = idempotency_key(event)
            if not key:
                return error_response(400, "missing_idempotency_key", "Authenticated predictions require an Idempotency-Key header.")
            claim_result, claim = claim_idempotency(user_id, key, request_fingerprint(model_input))
            if claim_result:
                return claim_result
            result["prediction_id"] = persist_prediction(user_id, model_input, result, claim)
            result["saved"] = True
            complete_idempotency(user_id, key, result)

        return response(200, result)
    except Exception:
        logger.exception("price_prediction_failed")
        return error_response(500, "internal_error", "The prediction service is temporarily unavailable.")
