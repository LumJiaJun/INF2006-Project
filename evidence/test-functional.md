# Test: Functional workflow

- **Objective:** Verify that the public CloudFront frontend loads and API Gateway invokes the health Lambda successfully.
- **Setup:** Terraform-managed development environment in `ap-southeast-1`, deployed from `src/infrastructure`.
- **Command / steps:**
  ```powershell
  $frontendUrl = terraform output -raw frontend_url
  $healthUrl = terraform output -raw health_url
  Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing
  Invoke-WebRequest -Uri $healthUrl -Headers @{ Origin = $frontendUrl } -UseBasicParsing
  ```
- **Expected result:** The frontend returns HTTP 200. The health endpoint returns HTTP 200 with service `airbnb-market-intelligence-api` and status `healthy`.
- **Actual result:** Passed. Both requests returned HTTP 200 and the health response contained the expected service and status values.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure`, `src/backend/health/handler.py`, and `tests/test_health.py`
