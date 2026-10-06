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
        "saved_predictions_used": body.get("context", {}).get("saved_predictions_used"),
    }


def history_item(source, user_id, index):
    item = dict(source)
    item["user_id"] = user_id
    item["created_at_prediction_id"] = f"{source['created_at']}#{index}"
    return item


def delete_history_items(table, items):
    for item in items:
        table.delete_item(
            Key={
                "user_id": item["user_id"],
                "created_at_prediction_id": item["created_at_prediction_id"],
            }
        )


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
    table = boto3.resource("dynamodb", region_name=args.region).Table(args.table_name)
    lambda_client = boto3.client("lambda", region_name=args.region)
    results = []
    created_items = []
    isolation = {"passed": False, "failures": ["isolation check did not run"]}
    try:
        for scenario_index, scenario in enumerate(chatbot_scenarios.SCENARIOS):
            user_id = f"deployed-chat-{scenario_index}-{run_id}"
            for item_index, source in enumerate(scenario["history"]):
                item = history_item(source, user_id, item_index)
                table.put_item(
                    Item=item,
                    ConditionExpression=(
                        "attribute_not_exists(user_id) AND "
                        "attribute_not_exists(created_at_prediction_id)"
                    ),
                )
                created_items.append(item)
            result = invoke_scenario(lambda_client, args.function_name, scenario, user_id)
            results.append(result)
            print(f"{'PASS' if result['passed'] else 'FAIL'} {result['name']}: {result['reply']}")
            for failure in result["failures"]:
                print(f"  - {failure}")

        owner_id = f"deployed-chat-isolation-owner-{run_id}"
        other_id = f"deployed-chat-isolation-other-{run_id}"
        owner_item = history_item(chatbot_scenarios.LATEST_PARIS, owner_id, 0)
        table.put_item(
            Item=owner_item,
            ConditionExpression=(
                "attribute_not_exists(user_id) AND "
                "attribute_not_exists(created_at_prediction_id)"
            ),
        )
        created_items.append(owner_item)
        latest_scenario = next(
            scenario
            for scenario in chatbot_scenarios.SCENARIOS
            if scenario["name"] == "latest_saved_prediction"
        )
        empty_scenario = next(
            scenario
            for scenario in chatbot_scenarios.SCENARIOS
            if scenario["name"] == "empty_history"
        )
        owner_result = invoke_scenario(
            lambda_client, args.function_name, latest_scenario, owner_id
        )
        other_result = invoke_scenario(
            lambda_client, args.function_name, empty_scenario, other_id
        )
        isolation_failures = []
        if not owner_result["passed"] or owner_result["saved_predictions_used"] != 1:
            isolation_failures.append("owner did not retrieve exactly one saved record")
        if not other_result["passed"] or other_result["saved_predictions_used"] != 0:
            isolation_failures.append("other user received owner history or an invalid reply")
        isolation = {
            "passed": not isolation_failures,
            "failures": isolation_failures,
            "owner_saved_predictions_used": owner_result["saved_predictions_used"],
            "other_saved_predictions_used": other_result["saved_predictions_used"],
        }
        print(
            f"{'PASS' if isolation['passed'] else 'FAIL'} user_partition_isolation: "
            f"owner={owner_result['saved_predictions_used']} other={other_result['saved_predictions_used']}"
        )
        for failure in isolation_failures:
            print(f"  - {failure}")
    finally:
        delete_history_items(table, created_items)

    auth_passed, auth_status = verify_unauthenticated_rejection(args.chat_url)
    print(f"{'PASS' if auth_passed else 'FAIL'} unauthenticated_api: HTTP {auth_status}")
    summary = {
        "scenario_count": len(results),
        "passed": sum(result["passed"] for result in results),
        "failed": sum(not result["passed"] for result in results),
        "unauthenticated_api_status": auth_status,
        "unauthenticated_api_passed": auth_passed,
        "user_partition_isolation": isolation,
        "results": results,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2))
    return 1 if summary["failed"] or not auth_passed or not isolation["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
