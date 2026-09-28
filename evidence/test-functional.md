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

## Authentication entry point and protected routes

- **Objective:** Verify that the deployed frontend has a working Cognito login entry point and that protected application routes enforce authentication.
- **Setup:** Cognito hosted UI, public application client, PKCE browser client, API Gateway JWT authorizer, and DynamoDB history table.
- **Command / steps:** Request the Cognito `/oauth2/authorize` URL and run `tests/smoke_api.ps1` against the deployed frontend and API.
- **Expected result:** Cognito redirects to its login page, all frontend authentication assets load with their correct content types, and unauthenticated protected calls return HTTP 401.
- **Actual result:** Passed. Cognito returned HTTP 302 to `/login`; frontend assets returned HTTP 200 with correct content types; history, saved prediction, and AI chat routes returned HTTP 401 without a token.
- **Date:** 2026-09-23
- **Actual authenticated journey:** Passed manually on 2026-09-28 with a consented test account during the explicitly temporary no-MFA test window. The tester signed up, logged in, saved a Bangkok estimate, viewed private history, and asked the protected assistant for the latest prediction. Cognito TOTP MFA was restored to `ON` and verified immediately afterward. No credentials, codes, or tokens were recorded.
- **Limitation:** The journey used one test account and does not replace a separate multi-user isolation browser test.
- **Artefact path:** `src/frontend/auth.js`, `src/frontend/app.js`, `src/infrastructure/auth.tf`, and `tests/smoke_api.ps1`

## Live market analytics

- **Objective:** Verify the user-facing market summary from API Gateway through Lambda and Athena to processed Parquet.
- **Setup:** Successful Glue transform and ten city partitions in the private data lake.
- **Command / steps:** Run `tests/smoke_api.ps1` against the deployed frontend and API.
- **Expected result:** `GET /analytics` returns HTTP 200 with ten typed city summaries, and the frontend assets include the analytics section.
- **Actual result:** Passed. The live route returned ten city summaries and the expanded smoke script completed successfully.
- **Date:** 2026-09-23
- **Artefact path:** `evidence/data-pipeline.md`, `src/backend/analytics/handler.py`, and `tests/smoke_api.ps1`
