import json
import logging
from datetime import UTC, datetime


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    request_context = event.get("requestContext", {}) if isinstance(event, dict) else {}
    request_id = request_context.get("requestId", getattr(context, "aws_request_id", "unknown"))

    logger.info(
        json.dumps(
            {
                "event": "health_check",
                "request_id": request_id,
                "status": "healthy",
            }
        )
    )

    body = {
        "service": "airbnb-market-intelligence-api",
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
    }

    return {
        "statusCode": 200,
        "headers": {
            "content-type": "application/json",
            "cache-control": "no-store",
        },
        "body": json.dumps(body),
    }
