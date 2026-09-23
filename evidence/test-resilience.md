# Test: Scalability, resilience, and recovery

## Bounded concurrency and overload behavior

- **Objective:** Observe API behavior under bounded concurrent health checks and verify that overload is rejected rather than silently corrupting responses.
- **Setup:** API Gateway HTTP API with a two-request burst and two-request-per-second default route limit, Lambda health function, and an account-wide Lambda concurrency quota of 10.
- **Command / steps:** Run `python tests/load_health.py --url <health-url> --requests 20 --concurrency 2`.
- **Expected result:** Every request returns either HTTP 200 or an explicit HTTP 429 throttle response; no backend 5xx response is accepted by the test.
- **Actual result:** Passed on 2026-09-23. Eighteen requests returned HTTP 200 and two returned HTTP 429. The run completed in 0.975 seconds; median latency was 86.58 ms and maximum latency was 163.60 ms.
- **Stress-test finding:** A deliberately excessive 50-request, concurrency-25 run produced 26 HTTP 200, 13 HTTP 429, and 11 HTTP 503 responses even after reducing the API limit. CloudWatch showed the account reaching its concurrency quota. API Gateway throttling is best-effort and cannot guarantee protection from the unusually low account-wide quota.
- **Improvement plan:** Request a higher Lambda concurrency quota before any higher-load deployment, repeat the load test, and consider route-specific usage controls if expected traffic increases. Do not claim high-scale readiness from this development account result.
- **Artefact path:** `tests/load_health.py`, `src/infrastructure/api.tf`, and `src/infrastructure/monitoring.tf`

## Prediction-history recovery

- **Objective:** Verify that application records have a managed recovery mechanism.
- **Setup:** DynamoDB prediction-history table with point-in-time recovery configured by Terraform.
- **Command / steps:** Run `aws dynamodb describe-continuous-backups --table-name <prediction-history-table>`.
- **Expected result:** Continuous backups and point-in-time recovery report `ENABLED`.
- **Actual result:** Passed on 2026-09-23. Both statuses were `ENABLED`.
- **Interpretation:** PITR protects history records against accidental writes or deletion within DynamoDB's recovery window. A restore creates a separate table and was not executed because it would add cost and require application cutover.
- **Artefact path:** `src/infrastructure/data.tf`
