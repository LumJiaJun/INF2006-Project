# Live Stack Test - 2026-10-09

Region ap-southeast-1, stack as deployed after the 9 October fixes (prediction
image `fix-libxml2`). Redacted: no account IDs, tokens, URLs with tokens, or
personal data. All steps were run by Nixon with AI assistance against the
team's own stack.

## Results

| Test | Tool or command | Result |
|------|-----------------|--------|
| Zero-drift and control verification | `tests/verify_cloud.ps1` (plan with the live image tag) | Passed: 148 managed resources, Terraform exit code 0; 5 Lambdas Active in 2 private subnets each; 5 alarms OK; CloudTrail logging without delivery error; DynamoDB PITR enabled; latest Glue run SUCCEEDED; frontend and data-lake public access blocks on; WAF attached; 1 confirmed SNS subscription. Redacted output: `cloud-verification-2026-10-09.md`. |
| Public smoke | `tests/smoke_api.ps1` | Passed: assets, security headers, prediction (EUR 65.98), 10 city analytics, protected routes, validation. |
| Saved-prediction recovery and chat validation | `tests/verify_live_recovery.py --i-confirm-authorized-target` (synthetic user, direct Lambda calls, records deleted) | Save 200; same-key replay 200 with the same ID; same key with changed input 409; new key 200 with a new ID; 2 history rows; chat `page` of `[]`, `{}`, `null`, `7` each 400; 0 records left. Run on both new images. |
| Chatbot evaluation | `tests/evaluate_deployed_chatbot.py` | 26 of 26 scenarios passed; user-partition isolation passed (owner saw 1 record, other user 0); anonymous API returned 401. |
| Security probes | `curl` | No-token `GET /history`, `POST /predictions`, `POST /chat` and a fake bearer token each 401; malformed JSON 400; injection-style city 400; unknown route 404; a request from a foreign origin received no CORS allow-origin header; the allowed origin permits the `idempotency-key` header; direct S3 origin returned 403. |
| Bounded load | `tests/load_health.py`, 60 requests, concurrency 4, `/health` | 42 x 200 and 18 x 429; median 370 ms, maximum 1373 ms. The 429 responses are the intended API throttle (1 to 2 requests per second per route), not an outage. This is a controlled-overload check, not a capacity benchmark. |
| DynamoDB point-in-time restore | `restore-table-to-point-in-time` of the history table at the latest restorable time into a temporary table | Table reached ACTIVE in about 3 minutes (created 18:54:28 +08, active before 18:58 +08). It was KMS-encrypted, had the same key schema (`user_id`, `created_at_prediction_id`), 1 item, and items identical to the source. The temporary table was then deleted and no restore table remained. |

## Interpretation and limits

- These tests show the stack behaved correctly at the tested time. They do not
  prove unlimited scale, cross-region recovery, or future drift-free operation.
- The restore test used a small table (1 item) and did not exercise cutover of
  the application to a restored table or restoration of a large table.
- The unit-tested lease takeover and completion-failure paths were not forced
  on the live stack; only their normal paths were observed live.
- Sign-up with a fresh account, MFA setup, and a real browser were not
  re-executed in this run.
