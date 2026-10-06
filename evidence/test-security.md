# Test: Security control

- **Objective:** Verify that users cannot bypass CloudFront to read frontend objects directly from S3 and that browser API access is restricted to the deployed frontend origin.
- **Setup:** Terraform-managed private frontend bucket, CloudFront Origin Access Control, and API Gateway CORS configuration.
- **Command / steps:**
  ```powershell
  $bucketName = terraform output -raw frontend_bucket_name
  $frontendUrl = terraform output -raw frontend_url
  $healthUrl = terraform output -raw health_url
  aws s3api get-public-access-block --bucket $bucketName
  Invoke-WebRequest -Uri "https://$bucketName.s3.ap-southeast-1.amazonaws.com/index.html" -UseBasicParsing
  Invoke-WebRequest -Uri $healthUrl -Headers @{ Origin = $frontendUrl } -UseBasicParsing
  ```
- **Expected result:** All S3 public access block settings are enabled, direct S3 object access returns HTTP 403, and the API response allows the exact CloudFront origin.
- **Actual result:** Passed. All four public access block settings were `true`, direct S3 access returned HTTP 403, and `Access-Control-Allow-Origin` matched the CloudFront frontend URL.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/frontend.tf` and `src/infrastructure/api.tf`

## Prediction input validation and least privilege

- **Objective:** Verify that malformed or unsupported prediction requests are rejected without exposing stack traces and that the prediction role cannot access unrelated AWS data services.
- **Setup:** Public `POST /predict` route, prediction handler validation, and a dedicated Lambda execution role.
- **Command / steps:** Run `python -m unittest discover -s tests -p "test_prediction.py" -v`, run `tests/smoke_api.ps1`, and inspect `aws_iam_role_policy.prediction_lambda_logs` in `src/infrastructure/prediction.tf`.
- **Expected result:** Invalid JSON, missing fields, unsupported categories, invalid coordinates, and unreasonable values return HTTP 400. The client receives safe errors. The Lambda role can write only to its own log group and the prediction-history table.
- **Actual result:** Passed. Prediction-handler tests passed, the live malformed request returned HTTP 400, and the role policy is limited to its log group plus `dynamodb:PutItem` on the prediction-history table.
- **Date:** 2026-09-23
- **Artefact path:** `tests/test_prediction.py`, `tests/smoke_api.ps1`, and `src/infrastructure/prediction.tf`

## Authentication and history isolation

- **Objective:** Verify that only valid Cognito JWTs can save or read history and that a caller cannot select another user's partition.
- **Setup:** Cognito authorization-code flow with PKCE, API Gateway JWT authorizer, and a DynamoDB table partitioned by the verified `sub` claim.
- **Command / steps:** Run `python -m unittest discover -s tests -p "test_*.py" -v` and `./tests/smoke_api.ps1 -FrontendUrl $frontendUrl -ApiBaseUrl $apiBaseUrl`.
- **Expected result:** Unauthenticated `POST /predictions` and `GET /history` requests return HTTP 401. The history function queries only the subject from API Gateway's verified claims.
- **Actual result:** Passed. Both deployed routes returned HTTP 401 without a token, and the handler test confirmed the query key comes from `requestContext.authorizer.jwt.claims.sub`.
- **Additional isolation result:** The handler test also passes when a caller supplies a different `user_id` query parameter; the verified JWT subject remains the only DynamoDB partition key.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/auth.tf`, `src/infrastructure/history.tf`, `src/backend/history/handler.py`, and `tests/test_history.py`

## AI chat history isolation

- **Objective:** Verify that the AI route requires a verified Cognito subject and supplies only that subject's recent prediction records to the model.
- **Setup:** API Gateway JWT authorizer, a dedicated chat Lambda role with `dynamodb:Query` only, and a DynamoDB table partitioned by `user_id`.
- **Command / steps:** Run `python tests/test_chat.py -v` and the deployed `tests/smoke_api.ps1` check without an authorization token.
- **Expected result:** Missing claims return HTTP 401. For an authenticated event, the Lambda queries the `user_id` partition using the validated JWT `sub`, projects only required prediction fields, requests at most ten rows, and uses a strongly consistent read so a newly saved prediction is available to the chat context without eventual-consistency delay.
- **Actual result:** Passed in focused handler tests on 2026-09-28. The test verified the bounded Bedrock request, injected prediction context, ten-row limit, and `ConsistentRead=True`; the deployed route rejected unauthenticated requests. The live Cognito browser journey is recorded below.
- **Artefact path:** `src/backend/chat/handler.py`, `src/infrastructure/chat.tf`, `tests/test_chat.py`, and `tests/smoke_api.ps1`

## Deployed AI and DynamoDB integration

- **Objective:** Verify the deployed chat Lambda can retrieve a user-scoped prediction and use it in a real Bedrock response.
- **Command / steps:** Run `tests/run_chat_integration.ps1` with the Terraform prediction-history table and chat Lambda outputs and the explicit authorization switch.
- **Expected result:** One synthetic prediction is inserted under a random test subject, the deployed Lambda returns a bounded answer describing that record, completion telemetry reports `history_record_count: 1`, and the synthetic row is deleted.
- **Actual result:** Passed on 2026-09-28. Claude Haiku returned an answer describing the synthetic Paris/Louvre prediction at EUR 123.45; CloudWatch recorded one retrieved history row; cleanup completed. This direct Lambda test proves model-plus-DynamoDB integration, while the separate anonymous API test proves the protected route rejects missing JWTs.
- **Artefact path:** `tests/run_chat_integration.ps1`, `src/backend/chat/handler.py`, and `src/infrastructure/outputs.tf`

## Authenticated browser journey

- **Objective:** Verify the real Cognito-to-API-to-DynamoDB-to-Bedrock journey from the website.
- **Steps:** A signed-in tester created a Cognito account, submitted a Bangkok estimate for a barn/entire-place listing with 2 guests, 1 bedroom, and 2 minimum nights, then asked the guide for the latest saved prediction.
- **Actual result:** Passed on 2026-09-28. The website displayed the saved `714.56 THB` Bangkok prediction in private history, and the chatbot returned the same Bangkok listing details and model version from DynamoDB context. No credentials, verification codes, or tokens were recorded.
- **Security result:** The chat response was user-scoped. The journey used the explicitly temporary no-MFA test window; Cognito TOTP MFA was restored to `ON` and verified immediately afterward. No credentials, verification codes, or tokens were recorded.
- **Known limitation:** The response is model-generated and must remain an estimate; this test proves retrieval and context flow, not universal factual accuracy for every question.

## Data-lake access control

- **Objective:** Verify that raw and processed analytical data are encrypted and unavailable through anonymous S3 requests.
- **Setup:** Terraform-managed data-lake bucket containing the raw listing object and processed Parquet.
- **Command / steps:** Run `aws s3api get-public-access-block`, `aws s3api get-bucket-encryption`, and an unauthenticated HTTPS request for `raw/listings/Listings.csv`.
- **Expected result:** All four public-access settings are enabled, default encryption is AES-256, and direct access returns HTTP 403.
- **Actual result:** Passed. The deployed bucket returned the expected controls and direct object access returned HTTP 403.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/data_lake.tf`

## Runtime-role blast radius

- **Objective:** Verify selected allowed and denied service-to-service permissions rather than relying only on policy inspection.
- **Setup:** Deployed prediction, history, and Glue execution roles.
- **Command / steps:** Run `aws iam simulate-principal-policy` for required and unrelated actions on named resources.
- **Expected result:** Prediction `dynamodb:PutItem`, history `dynamodb:Query`, and Glue raw-listing reads are allowed. Prediction raw-data reads, history table scans, and Glue raw-review reads are denied by omission.
- **Actual result:** Passed. Required operations returned `allowed`; all three unrelated operations returned `implicitDeny`.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/prediction.tf`, `src/infrastructure/history.tf`, `src/infrastructure/data_lake.tf`, and `evidence/serverless-zero-trust-review.md`

## Edge response hardening

- **Objective:** Verify defense-in-depth headers on the public frontend.
- **Setup:** CloudFront response headers policy attached to the default cache behavior.
- **Command / steps:** Run `tests/smoke_api.ps1` against the deployed frontend and API.
- **Expected result:** The frontend includes CSP, HSTS, `X-Content-Type-Options`, and `X-Frame-Options`.
- **Actual result:** Passed. All four headers were present after CloudFront propagation and invalidation.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/frontend.tf` and `tests/smoke_api.ps1`

## Automated SAST and DAST

- **Objective:** Detect source-level security defects continuously and perform passive dynamic checks against an explicitly approved deployment.
- **Setup:** CodeQL security-extended queries for Python and JavaScript plus an OWASP ZAP baseline workflow protected by the GitHub `development` environment.
- **Command / steps:** Push or open a pull request to run `.github/workflows/codeql.yml`. After deployment, configure `DAST_TARGET_URL` and the exact `DAST_ALLOWED_HOST`, then run `.github/workflows/dast.yml` manually or allow the successful deployment workflow to trigger it.
- **Expected result:** CodeQL uploads security analysis for both languages. ZAP accepts only an allowlisted HTTPS host, performs passive scanning, uploads HTML, JSON, and Markdown reports, and fails on scan errors plus new or explicitly actionable findings.
- **Actual result:** CodeQL passed for both languages on 2026-09-28. GitHub DAST run `36689377727` executed on 2026-09-30. Target validation, reachability, scanning, and report upload passed; the enforcement step failed on six warning categories and preserved artifact `zap-baseline-36689377727`. The corrected pinned local scan on 2 October crawled 175 URLs and passed with exit code 0, 0 failed rules, 0 warnings, 63 passed rules, and 4 narrowly reviewed ignored rules. After CloudFront stopped rewriting WAF 403 responses to HTTP 200, a second pinned scan on 3 October also passed with 0 failures and 0 warnings. Its crawl was intentionally smaller because blocked and missing paths retained HTTP 403. The corrected GitHub workflow was then manually dispatched as run `36699009812`; target validation, reachability, the passive scan, report upload, and the overall job completed successfully.
- **Date:** 2026-09-30
- **Artefact path:** `.github/workflows/codeql.yml`, `.github/workflows/dast.yml`, `evidence/ci-cd.md`, and `evidence/github-security-runs-2026-10-06.md`

## AI prompt-injection boundary

- **Objective:** Verify that malicious user text remains untrusted request data and cannot replace the assistant's system instructions.
- **Setup:** Chat handler unit test with authenticated synthetic claims, bounded fake history, and a fake Bedrock client.
- **Command / steps:** Run `python -m unittest tests.test_chat.ChatHandlerTests.test_wraps_prompt_injection_as_untrusted_request_data -v`.
- **Expected result:** The malicious instruction appears only inside the JSON-wrapped user message, the trusted system prompt remains unchanged, and the handler returns a bounded response without logging prompt text.
- **Actual result:** Passed locally and through two deployed direct-Lambda checks using a synthetic subject. The assistant refused requests for its system prompt, credentials, and another user's history. A property-purchase question received a direct scope limitation and an offer to explore a supported hosting scenario instead. The retest did not describe nightly price as revenue, income, profitability, valuation, return, or investment potential. Recent CloudWatch events contained request ID, page, history count, and token counts but neither test question.
- **Date:** 2026-10-01
- **Artefact path:** `src/backend/chat/handler.py`, `tests/test_chat.py`, `evidence/encryption-review-2026-10-01.md`, and `evidence/consultation-improvements-2026-10-01.md`

## Authorization and egress regression

- **Objective:** Prevent protected routes, purpose-specific execution roles, or private Lambda egress from becoming broader during later changes.
- **Setup:** Static regression tests inspect the Terraform authorization and network contracts without requiring AWS credentials.
- **Command / steps:** Run `python -m unittest tests.test_infrastructure_security -v`.
- **Expected result:** All protected routes require the Cognito JWT authorizer, all five Lambdas retain separate purpose-specific roles, and Lambda HTTPS egress is limited to the VPC and S3/DynamoDB managed prefix lists rather than `0.0.0.0/0`.
- **Actual result:** Passed as part of the 37-test local preflight. Terraform formatting and validation also passed after the egress change.
- **Date:** 2026-10-02
- **Artefact path:** `tests/test_infrastructure_security.py`, `src/infrastructure/network.tf`, and `evidence/iam-rbac-review-2026-10-02.md`
