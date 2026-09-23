import json
import logging
import os
import time

import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

DATABASE_NAME = os.environ.get("ATHENA_DATABASE_NAME")
TABLE_NAME = os.environ.get("ATHENA_TABLE_NAME")
WORKGROUP_NAME = os.environ.get("ATHENA_WORKGROUP_NAME")
QUERY_TIMEOUT_SECONDS = 12
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
CITY_SUMMARY_QUERY = """
SELECT
    city,
    COUNT(*) AS listing_count,
    ROUND(AVG(price), 2) AS average_nightly_price,
    ROUND(approx_percentile(price, 0.5), 2) AS median_nightly_price,
    ROUND(AVG(review_scores_rating), 1) AS average_rating
FROM {table_name}
GROUP BY city
ORDER BY city
"""

_athena = None


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            "cache-control": "public, max-age=300" if status_code == 200 else "no-store",
        },
        "body": json.dumps(body),
    }


def athena_client():
    global _athena
    if _athena is None:
        _athena = boto3.client("athena")
    return _athena


def wait_for_query(client, execution_id):
    deadline = time.monotonic() + QUERY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        execution = client.get_query_execution(QueryExecutionId=execution_id)
        state = execution["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            return
        if state in {"FAILED", "CANCELLED"}:
            raise RuntimeError(f"Athena query ended in state {state}")
        time.sleep(0.2)
    client.stop_query_execution(QueryExecutionId=execution_id)
    raise TimeoutError("Athena query exceeded the application timeout")


def parse_rows(result):
    rows = result.get("ResultSet", {}).get("Rows", [])
    if len(rows) < 2:
        return []
    columns = [item.get("VarCharValue", "") for item in rows[0]["Data"]]
    parsed = []
    for row in rows[1:]:
        values = [item.get("VarCharValue") for item in row.get("Data", [])]
        record = dict(zip(columns, values, strict=False))
        parsed.append(
            {
                "city": record["city"],
                "currency": CURRENCY_BY_CITY[record["city"]],
                "listing_count": int(record["listing_count"]),
                "average_nightly_price": float(record["average_nightly_price"]),
                "median_nightly_price": float(record["median_nightly_price"]),
                "average_rating": (
                    float(record["average_rating"]) if record.get("average_rating") is not None else None
                ),
            }
        )
    return parsed


def lambda_handler(event, context):
    try:
        client = athena_client()
        # Clients cannot supply SQL; this fixed query is the complete public analytics surface.
        query = CITY_SUMMARY_QUERY.format(table_name=TABLE_NAME)
        started = client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": DATABASE_NAME},
            WorkGroup=WORKGROUP_NAME,
        )
        execution_id = started["QueryExecutionId"]
        wait_for_query(client, execution_id)
        items = parse_rows(
            client.get_query_results(QueryExecutionId=execution_id, MaxResults=100)
        )
        logger.info(
            json.dumps(
                {
                    "event": "city_analytics_read",
                    "request_id": event.get("requestContext", {}).get("requestId", "unknown"),
                    "city_count": len(items),
                    "query_execution_id": execution_id,
                }
            )
        )
        return response(
            200,
            {
                "items": items,
                "count": len(items),
                "price_basis": "Local currency for each city",
                "scope": "Positive prices up to each city's observed 99th percentile",
            },
        )
    except Exception:
        logger.exception("city_analytics_read_failed")
        return response(
            500,
            {"error": {"code": "internal_error", "message": "Market analytics are unavailable."}},
        )
