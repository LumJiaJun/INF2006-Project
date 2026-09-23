# Monitoring / logging evidence

- **What is monitored:** Health Lambda invocations and application health events in a dedicated CloudWatch log group with 14-day retention.
- **Operational test / query:** Invoke `terraform output -raw health_url`, then run `aws logs tail '/aws/lambda/airbnb-market-intelligence-dev-health' --since 10m --format short`.
- **Result:** CloudWatch contained an INFO event named `health_check` with status `healthy` after the live API request.
- **Interpretation:** API Gateway invoked the Lambda successfully and the function can write through its scoped logging policy. This confirms basic logging, not complete production observability.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/api.tf` and `src/backend/health/handler.py`
