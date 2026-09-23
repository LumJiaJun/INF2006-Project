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

## Live price prediction

- **Objective:** Verify the complete user workflow from the public API through API Gateway and the container-image Lambda to a real model estimate.
- **Setup:** Deployed model version `1.0.0` in prediction image `1.0.2` with 2 GB Lambda memory.
- **Command / steps:**
  ```powershell
  $frontendUrl = terraform -chdir=src/infrastructure output -raw frontend_url
  $apiBaseUrl = (terraform -chdir=src/infrastructure output -raw health_url) -replace '/health$', ''
  ./tests/smoke_api.ps1 -FrontendUrl $frontendUrl -ApiBaseUrl $apiBaseUrl
  ```
- **Expected result:** Health returns HTTP 200, valid Paris listing details return a numeric EUR estimate, and malformed JSON returns HTTP 400.
- **Actual result:** Passed. The live model returned 65.98 EUR with model version `1.0.0`; malformed JSON returned HTTP 400 with code `invalid_json`.
- **Date:** 2026-09-23
- **Artefact path:** `tests/smoke_api.ps1`, `src/backend/predict/handler.py`, and `src/infrastructure/prediction.tf`
