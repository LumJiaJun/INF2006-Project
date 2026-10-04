import argparse
import importlib.util
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import boto3


EVALUATOR_PATH = Path(__file__).with_name("evaluate_chatbot.py")
SPEC = importlib.util.spec_from_file_location("chatbot_scenarios", EVALUATOR_PATH)
chatbot_scenarios = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chatbot_scenarios)


def invoke_scenario(client, function_name, scenario, user_id):
    event = chatbot_scenarios.event(scenario["question"])
    event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"] = user_id
    response = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(event).encode("utf-8"),
    )
    envelope = json.loads(response["Payload"].read())
    body = json.loads(envelope["body"])
    reply = body.get("reply", "")
    failures = [] if envelope["statusCode"] == 200 else [f"HTTP {envelope['statusCode']}"]
    failures.extend(chatbot_scenarios.evaluate_text(reply, scenario))
    return {
        "name": scenario["name"],
        "passed": not failures,
        "failures": failures,
        "reply": reply,
    }


def verify_unauthenticated_rejection(chat_url):
    request = urllib.request.Request(
        chat_url,
        data=json.dumps({"message": "hello", "page": "index.html"}).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as error:
        return error.code == 401, error.code
    return False, 200


def main():
    parser = argparse.ArgumentParser(description="Evaluate the deployed chatbot and isolated DynamoDB history.")
    parser.add_argument("--function-name", required=True)
    parser.add_argument("--table-name", required=True)
    parser.add_argument("--chat-url", required=True)
    parser.add_argument("--region", default="ap-southeast-1", choices=["ap-southeast-1"])
    parser.add_argument("--i-confirm-authorized-target", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.i_confirm_authorized_target:
        parser.error("Pass --i-confirm-authorized-target only for an AWS environment you may test.")

    run_id = uuid.uuid4().hex
    history_user_id = f"deployed-chat-history-{run_id}"
    empty_user_id = f"deployed-chat-empty-{run_id}"
    table = boto3.resource("dynamodb", region_name=args.region).Table(args.table_name)
    lambda_client = boto3.client("lambda", region_name=args.region)
    items = []
    for index, source in enumerate(
        (chatbot_scenarios.LATEST_PARIS, chatbot_scenarios.OLDER_NEW_YORK)
    ):
        item = dict(source)
        item["user_id"] = history_user_id
        item["created_at_prediction_id"] = f"{source['created_at']}#{index}"
        items.append(item)

    results = []
    try:
        for item in items:
            table.put_item(Item=item, ConditionExpression="attribute_not_exists(user_id)")
        for scenario in chatbot_scenarios.SCENARIOS:
            user_id = history_user_id if scenario["history"] else empty_user_id
            result = invoke_scenario(lambda_client, args.function_name, scenario, user_id)
            results.append(result)
            print(f"{'PASS' if result['passed'] else 'FAIL'} {result['name']}: {result['reply']}")
            for failure in result["failures"]:
                print(f"  - {failure}")
    finally:
        for item in items:
            table.delete_item(
                Key={
                    "user_id": history_user_id,
                    "created_at_prediction_id": item["created_at_prediction_id"],
                }
            )

    auth_passed, auth_status = verify_unauthenticated_rejection(args.chat_url)
    print(f"{'PASS' if auth_passed else 'FAIL'} unauthenticated_api: HTTP {auth_status}")
    summary = {
        "scenario_count": len(results),
        "passed": sum(result["passed"] for result in results),
        "failed": sum(not result["passed"] for result in results),
        "unauthenticated_api_status": auth_status,
        "unauthenticated_api_passed": auth_passed,
        "results": results,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2))
    return 1 if summary["failed"] or not auth_passed else 0


if __name__ == "__main__":
    raise SystemExit(main())
