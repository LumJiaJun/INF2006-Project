# Monitoring / logging evidence

- **What is monitored:** Health Lambda invocations and application health events in a dedicated CloudWatch log group with 14-day retention.
- **Operational test / query:** Invoke `terraform output -raw health_url`, then run `aws logs tail '/aws/lambda/airbnb-market-intelligence-dev-health' --since 10m --format short`.
- **Result:** CloudWatch contained an INFO event named `health_check` with status `healthy` after the live API request.
- **Interpretation:** API Gateway invoked the Lambda successfully and the function can write through its scoped logging policy. This confirms basic logging, not complete production observability.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/api.tf` and `src/backend/health/handler.py`

## Prediction runtime

- **What is monitored:** Prediction Lambda startup, duration, memory allocation, errors, and application events in a dedicated 14-day CloudWatch log group.
- **Operational test / query:** Invoke `POST /predict`, then run `aws logs tail '/aws/lambda/airbnb-market-intelligence-dev-prediction' --since 5m --format short`.
- **Result:** CloudWatch recorded the `price_prediction` event and model version without logging listing inputs. Initial 1 GB cold latency was 13.8 seconds. Increasing memory to 2 GB reduced a fresh-environment request to approximately 3.0 to 3.3 seconds. Warm requests measured 59 to 70 ms.
- **Interpretation:** The memory increase materially reduces cold-start timeout risk for the scientific Python container. More load samples are required before making a scalability claim.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/prediction.tf`, `src/backend/predict/handler.py`, and `evidence/prediction-runtime.md`

## Analytics query operations

- **What is monitored:** Glue job status and duration, Athena bytes scanned and execution time, and analytics Lambda application events in a dedicated 14-day log group.
- **Operational test / query:** Run the Glue job, inspect it with `aws glue get-job-run`, invoke `GET /analytics`, inspect `aws athena get-query-execution`, and tail `/aws/lambda/airbnb-market-intelligence-dev-analytics`.
- **Result:** Glue succeeded in 90 seconds. A recorded successful Athena request scanned 566,077 bytes, used 574 ms of engine time, and completed in 697 ms. Lambda logged `city_analytics_read` with `city_count` 10 and no listing-level data.
- **Interpretation:** The pipeline and query are observable through managed metrics and structured logs. This is a point observation, not a sustained-load result.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/data_lake.tf`, `src/infrastructure/analytics.tf`, and `evidence/data-pipeline.md`

## Alarms and notification path

- **What is monitored:** API Gateway 5xx responses plus prediction and analytics Lambda errors over five-minute periods. A CloudWatch dashboard displays API request/error counts and Lambda p95 duration/error metrics.
- **Operational test / query:** Set the prediction-error alarm to `ALARM` with `aws cloudwatch set-alarm-state`, inspect action history, then reset it to `OK`.
- **Result:** The first action failed because the AWS-managed SNS key did not grant CloudWatch access. After replacing it with a rotating customer-managed key scoped to this account's named alarms, action history reported `Successfully executed action` for the encrypted SNS topic. The test alarm was reset to `OK`.
- **Interpretation:** Alarm-to-topic publishing works. The topic currently has no human subscription, so operators must add a confirmed endpoint outside the submission before relying on notifications.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/monitoring.tf`
