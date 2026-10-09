"""Operator check of saved-prediction idempotency and chat input validation on the deployed Lambdas.

Uses a synthetic user, invokes the Lambdas directly (no Cognito token), and deletes every
record it creates. Run only against a stack you are authorised to test:
    python tests/verify_live_recovery.py --i-confirm-authorized-target
"""
import argparse
import sys

if "--i-confirm-authorized-target" not in sys.argv:
    sys.exit("Refusing to run: pass --i-confirm-authorized-target for a stack you are authorised to test.")
import json
import subprocess
import time
import uuid

import boto3

REGION = "ap-southeast-1"
PRED = "airbnb-market-intelligence-dev-prediction"
CHAT = "airbnb-market-intelligence-dev-chat"
HIST = "airbnb-market-intelligence-dev-prediction-history"
IDEM = "airbnb-market-intelligence-dev-prediction-idempotency"

lam = boto3.client("lambda", region_name=REGION)
ddb = boto3.resource("dynamodb", region_name=REGION)
user = f"sanity-verify-{uuid.uuid4().hex[:12]}"

payload = {
    "city": "Bangkok", "neighbourhood": "Bang Bon", "property_type": "Barn", "room_type": "Entire place",
    "latitude": 13.74079, "longitude": 100.62663, "accommodates": 2, "bedrooms": 1, "minimum_nights": 2,
    "review_scores_rating": 95, "host_total_listings_count": 1, "amenities_count": 8,
    "instant_bookable": False, "host_is_superhost": False, "host_identity_verified": True,
}


def event(body, key=None):
    ev = {"body": json.dumps(body), "requestContext": {"requestId": "verify", "authorizer": {"jwt": {"claims": {"sub": user}}}}}
    if key:
        ev["headers"] = {"Idempotency-Key": key}
    return ev


def invoke(fn, ev):
    out = lam.invoke(FunctionName=fn, Payload=json.dumps(ev).encode())
    env = json.loads(out["Payload"].read())
    return env.get("statusCode"), json.loads(env["body"]) if env.get("body") else env


# the real model uses observed categories; discover a valid room_type by trying the documented value set
results = []
key = "verify-key-1"
code, body = invoke(PRED, event(payload, key))
if code == 400:
    print("validation detail:", body)
results.append(("save with key", code, body.get("saved")))
first_id = body.get("prediction_id")
code2, body2 = invoke(PRED, event(payload, key))
results.append(("replay same key", code2, body2.get("prediction_id") == first_id))
changed = dict(payload, amenities_count=9)
code3, body3 = invoke(PRED, event(changed, key))
results.append(("same key, changed input", code3, body3.get("error", {}).get("code")))
code4, body4 = invoke(PRED, event(payload, "verify-key-2"))
results.append(("different key = new submission", code4, body4.get("prediction_id") != first_id))

items = ddb.Table(HIST).query(KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq(user))["Items"]
results.append(("history rows for test user (expect 2)", len(items), None))

for bad in ([], {}, None, 7):
    c, b = invoke(CHAT, event({"message": "hi", "page": bad}))
    results.append((f"chat page={bad!r}", c, b.get("error", {}).get("code")))

for r in results:
    print(r)

# clean up every record created for the synthetic user
for it in items:
    ddb.Table(HIST).delete_item(Key={"user_id": user, "created_at_prediction_id": it["created_at_prediction_id"]})
for k in ("verify-key-1", "verify-key-2"):
    ddb.Table(IDEM).delete_item(Key={"user_id": user, "idempotency_key": k})
left_h = ddb.Table(HIST).query(KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq(user))["Items"]
left_i = [ddb.Table(IDEM).get_item(Key={"user_id": user, "idempotency_key": k}).get("Item") for k in ("verify-key-1", "verify-key-2")]
print("cleanup: history left =", len(left_h), "| idempotency left =", sum(1 for x in left_i if x))
