import json
import logging
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key


logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("HISTORY_TABLE_NAME")
_history_table = None


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
        },
        "body": json.dumps(body),
    }


def authenticated_user_id(event):
    if not isinstance(event, dict):
        return None
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("jwt", {})
        .get("claims", {})
        .get("sub")
    )


def history_table():
    global _history_table
    if _history_table is None:
        if not TABLE_NAME:
            raise RuntimeError("HISTORY_TABLE_NAME is not configured")
        _history_table = boto3.resource("dynamodb").Table(TABLE_NAME)
    return _history_table


def json_value(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_value(item) for item in value]
    return value


def lambda_handler(event, context):
    user_id = authenticated_user_id(event)
    if not user_id:
        return response(401, {"error": {"code": "unauthenticated", "message": "Sign in is required."}})

    try:
        result = history_table().query(
            KeyConditionExpression=Key("user_id").eq(user_id),
            ScanIndexForward=False,
            Limit=50,
        )
        items = [json_value(item) for item in result.get("Items", [])]
        logger.info(
            json.dumps(
                {
                    "event": "prediction_history_read",
                    "request_id": event.get("requestContext", {}).get("requestId", "unknown"),
                    "item_count": len(items),
                }
            )
        )
        return response(200, {"items": items, "count": len(items)})
    except Exception:
        logger.exception("prediction_history_read_failed")
        return response(
            500,
            {"error": {"code": "internal_error", "message": "Prediction history is unavailable."}},
        )
