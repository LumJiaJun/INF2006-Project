# Live Deployment and Test Evidence - 2026-09-28

## Deployment

The `nixon` branch was deployed to the configured Singapore AWS development account using the shared, KMS-encrypted S3 Terraform backend.

- The prediction ECR repository was created first because the application stack references an immutable image tag.
- The evaluated model artifact was built into the Linux `amd64` Lambda image and pushed with immutable tag `1.0.3`.
- Terraform created the remaining serverless application resources, then reported no infrastructure drift after deployment.
- The supplied `Listings.csv` source file was uploaded to the private data lake.
- The Glue transform completed successfully in 93 seconds and wrote the processed analytics data used by the live endpoint.

The initial full apply exposed a Terraform dependency race: the default HTTP API stage referenced `POST /chat` route settings before that route existed. `src/infrastructure/api.tf` now declares the route dependencies explicitly. The follow-up apply completed successfully.

## Live Functional and Security Results

`tests/smoke_api.ps1` passed against Terraform-derived frontend and API URLs:

- Frontend assets returned their expected content types.
- CloudFront returned CSP, HSTS, MIME-sniffing, anti-framing, permissions, opener, and resource policies.
- `GET /health` returned healthy.
- `POST /predict` returned a Paris estimate of `EUR 65.98` from the deployed evaluated model.
- `GET /analytics` returned ten city summaries from the processed real dataset.
- Protected history and AI routes rejected unauthenticated requests.
- A malformed prediction request was rejected safely.

The first public prediction immediately after deployment returned HTTP 503 during warm-up, then the same route succeeded on retry. The API server-error alarm correctly entered `ALARM` for that event and later returned to `OK` after the evaluation window without further 5xx responses.

## Bounded Load Results

The approved, hostname-allowlisted JMeter journey used five threads, a five-second ramp, and a 15-second duration:

- 62 CloudFront requests
- 0 failures
- 732.8 ms average response time
- 1,552 ms maximum response time

The bounded health-route test used 20 requests at concurrency two:

- 18 HTTP 200 responses
- 2 HTTP 429 responses
- No HTTP 5xx responses
- 88.93 ms median latency

The 429 responses match the configured two-request-per-second API Gateway limit and demonstrate controlled overload rejection. This is not a DDoS or unlimited-scale claim.

## AWS Control Review

- CloudFront was `Deployed`, enabled, and redirects viewers to HTTPS.
- DynamoDB was `ACTIVE`, on-demand, encrypted, and had point-in-time recovery enabled.
- Frontend and data-lake S3 buckets had all four public-access-block settings enabled.
- All five CloudWatch alarms were `OK` after the post-deployment evaluation window.
- Terraform returned `No changes` after deployment.

## Passive DAST Result

The pinned OWASP ZAP baseline crawled 26 frontend URLs. It found no high-risk alerts. After the response-header update, it passed the CSP and Permissions Policy checks.

Five warning categories remain and keep the strict DAST workflow failing until they receive explicit review:

1. Cache-control and cacheable-content notices for intentional static CloudFront caching.
2. Informational student-code comment notices without secrets or internal paths.
3. A potential form-attribute XSS heuristic caused by crawler query parameters. The frontend uses fixed templates and safe DOM APIs for user data; this needs a regression test rather than a blanket suppression.
4. CloudFront's managed `Server` header, which cannot be removed by the response-headers policy.
5. Missing cross-origin embedder policy. Cross-origin isolation is not required by the application and enabling it may restrict future Cognito or third-party integrations.

The full ZAP HTML, JSON, and Markdown reports are retained only in ignored `tmp/zap-live-after-headers-20260928/` output because they include run-specific URLs and scanner artefacts.

## ECR Scan Limitation

ECR scan-on-push is enabled. An additional manual scan was attempted, but AWS returned `LimitExceededException` because the per-image scan quota had already been reached. This is not evidence of a clean image scan. Review ECR's completed scan findings after the quota window before presenting image-vulnerability results.

## Prioritized Improvements

1. Add a focused frontend regression test that proves crafted query values never reach executable DOM sinks, then review whether the ZAP form-attribute alert can be safely classified as a false positive.
2. Keep DAST strict until each remaining warning has an evidence-backed disposition. Do not use a global ZAP ignore rule for potential XSS findings.
3. Add a verified non-personal SNS subscriber and exercise a test alarm so operational notification delivery is evidenced.
4. Configure the protected GitHub DAST variables and run the repository workflow against the approved live host.
5. Repeat the bounded live load profile after requesting a higher Lambda concurrency quota, then compare CloudWatch p95 latency and throttle metrics across runs.
6. Review ECR scan results after its quota resets and retain a redacted image-scan export as evidence.
