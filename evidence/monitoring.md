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
