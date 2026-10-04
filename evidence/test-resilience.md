# Test: Scalability, resilience, and recovery

## Bounded concurrency and overload behavior

- **Objective:** Observe API behavior under bounded concurrent health checks and verify that overload is rejected rather than silently corrupting responses.
- **Historical setup (2026-09-23):** API Gateway HTTP API with a two-request burst and two-request-per-second default route limit, Lambda health function, and an account-wide Lambda concurrency quota of 10.
- **Command / steps:** Run `python tests/load_health.py --url <health-url> --requests 20 --concurrency 2`.
- **Expected result:** Every request returns either HTTP 200 or an explicit HTTP 429 throttle response; no backend 5xx response is accepted by the test.
- **Actual result:** Passed on 2026-09-23. Eighteen requests returned HTTP 200 and two returned HTTP 429. The run completed in 0.975 seconds; median latency was 86.58 ms and maximum latency was 163.60 ms.
- **Historical stress-test finding:** A deliberately excessive 50-request, concurrency-25 run produced 26 HTTP 200, 13 HTTP 429, and 11 HTTP 503 responses even after reducing the API limit. CloudWatch showed the account reaching the then-current concurrency quota. API Gateway throttling is best-effort and cannot guarantee protection from an unusually low account-wide quota.
- **Improvement plan:** Request a higher Lambda concurrency quota before any higher-load deployment, repeat the load test, and consider route-specific usage controls if expected traffic increases. Do not claim high-scale readiness from this development account result.
- **Artefact path:** `tests/load_health.py`, `src/infrastructure/api.tf`, and `src/infrastructure/monitoring.tf`

### Approved-quota stress retest

- **Objective:** Recheck bounded overload behavior after the account-level Lambda concurrency quota increase.
- **Setup:** AWS Lambda account quota of 1,000 in `ap-southeast-1`; HTTPS API Gateway endpoints; 100 requests with concurrency 10 against `/health` and `/predict`. This is an authorized application stress test, not a DDoS test.
- **Actual result on 2026-09-29:** Health returned 53 HTTP 200 and 47 HTTP 429 responses at 33.95 requests/second. Prediction returned 62 HTTP 200 and 38 HTTP 429 responses at 18.91 requests/second. No HTTP 5xx responses occurred. CloudWatch showed zero Lambda errors and zero Lambda throttles for the health function; the prediction function remained `Active` with a successful update state and no Lambda-level errors or throttles reported for the observation window.
- **Interpretation:** API Gateway route throttling rejected excess traffic before it became a Lambda failure. The result demonstrates controlled overload handling at this test size, but it does not prove production-scale capacity or DDoS protection.
- **Artefact path:** `tests/load_health.py` and the 2026-09-29 terminal run output.

### Bounded denial-of-service control retest

- **Objective:** Verify that a short authorized traffic burst is handled by explicit throttling without backend errors, and confirm that the CloudFront WAF blocks a representative managed-rule attack signature.
- **Setup:** Team-owned development deployment, exact-host allowlisting, a hard cap of 100 requests and concurrency 10, API Gateway route throttling, CloudFront WAF managed common rules, and CloudWatch metrics. This was a bounded load and control test, not a DDoS attack.
- **Command / steps:** Run `python tests/load_health.py --url <health-url> --requests 100 --concurrency 10 --allowed-host <api-host> --confirm-authorized-target`; request the normal CloudFront page and one URL-encoded XSS probe; then inspect API Gateway 5xx, health Lambda errors and throttles, WAF sampled requests, and alarm states.
- **Expected result:** Responses are HTTP 200 or controlled HTTP 429 only; there are no API 5xx, Lambda errors, or Lambda throttles; the normal frontend returns HTTP 200; the managed-rule probe returns HTTP 403; WAF records a sampled common-rule request; and all alarms remain OK.
- **Actual result:** Passed on 2026-10-04. The bounded burst returned 60 HTTP 200 and 40 HTTP 429 responses at 27.89 requests per second. Median latency was 311.93 ms and maximum latency was 967.88 ms. API 5xx, health Lambda errors, and health Lambda throttles were all zero in the observation window. The normal frontend returned HTTP 200, the XSS probe returned HTTP 403, the WAF common-rule sample count was one, and all five alarms remained OK.
- **Interpretation:** API Gateway throttling controlled the direct API burst. The CloudFront WAF protects the frontend distribution, not the public API Gateway hostname, and its 2,000-request rate rule was deliberately not saturated. This result does not claim DDoS certification, unlimited scale, volumetric-attack resistance, or validation of the WAF rate-limit threshold.
- **Date:** 2026-10-04
- **Artefact path:** `tests/load_health.py`, `src/infrastructure/api.tf`, `src/infrastructure/security_edge.tf`, and `src/infrastructure/monitoring.tf`

## Prediction-history recovery

- **Objective:** Verify that application records have a managed recovery mechanism.
- **Setup:** DynamoDB prediction-history table with point-in-time recovery configured by Terraform.
- **Command / steps:** Run `aws dynamodb describe-continuous-backups --table-name <prediction-history-table>`.
- **Expected result:** Continuous backups and point-in-time recovery report `ENABLED`.
- **Actual result:** Passed on 2026-09-23. Both statuses were `ENABLED`.
- **Interpretation:** PITR protects history records against accidental writes or deletion within DynamoDB's recovery window. A restore creates a separate table and was not executed because it would add cost and require application cutover.
- **Artefact path:** `src/infrastructure/data.tf`

## Cross-region recovery status

- **Current result:** Not deployed or tested. The application has regional DynamoDB PITR and Terraform recreation evidence, but no second-region replica, S3 replication path, or tested endpoint cutover.
- **Reason:** A DR region, RPO/RTO, data-residency decision, and cost budget are required before creating cross-region resources.
- **Plan:** See `evidence/cross-region-recovery-plan.md`.

## Authenticated prediction idempotency

- **Objective:** Prevent a client retry after an uncertain response from creating duplicate prediction-history records.
- **Setup:** Authenticated `/predictions` requests, a required `Idempotency-Key` header, and an encrypted on-demand DynamoDB idempotency table with 24-hour TTL.
- **Command / steps:** Run `python -m unittest discover -s tests -p "test_prediction.py" -v` and inspect `src/backend/predict/handler.py` and `src/infrastructure/data.tf`.
- **Expected result:** A missing key returns HTTP 400; a repeated key with the same request replays the original response; a key reused for different input is rejected with HTTP 409.
- **Actual result:** Passed in 29-test local suite. The unit test confirms the original saved record is replayed and only one history item is written. Live browser deployment now sends a fresh key per authenticated submission; a live retry test should be repeated after the next authenticated journey.
- **Artefact path:** `src/backend/predict/handler.py`, `src/infrastructure/data.tf`, and `tests/test_prediction.py`
