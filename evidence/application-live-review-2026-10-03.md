# Application Live Review - 2026-10-03

## Local-first gate

The complete offline preflight ran before cloud changes. It passed 38 Python
tests, Python compilation, five JavaScript syntax checks, Terraform formatting
and validation, deterministic synthetic model training, and loopback frontend,
health, analytics, schema, and prediction requests.

## Reviewed deployment

The empty application state was rebuilt in two reviewed stages. The ECR
bootstrap plan added two resources with no changes or destruction. After the
immutable prediction image was pushed, the full plan added 123 resources with
no changes or destruction. The real listings CSV was uploaded with AES-256
server-side encryption, and Glue run
`jr_b3fc104ce93c03c82b9fa66ef8b8b3ad66a1592ca12942e3d57e2d6a7de8bfd6`
completed successfully in 108 seconds.

## Application improvements

- The browser retries one transient HTTP 502, 503, or 504 prediction response
  and displays a model-warming state. This addresses a first request immediately
  after the clean image deployment that returned HTTP 503 while Lambda completed
  model initialization. Subsequent smoke requests passed.
- The estimate result now offers three one-input what-if scenarios: five more
  amenities, one more guest, and toggled superhost status. The interface states
  that these are model scenarios, not future-price forecasts.
- Mobile navigation spacing, hero sizing, and what-if controls were tightened.
- Authenticated prediction records now retain amenities, host listing count,
  booking and host signals, and optional rating. Exact coordinates remain
  excluded.
- The chat Lambda projects the safe retained fields, reads at most ten records
  for the verified JWT subject, and returns a count of records used. The frontend
  displays that count below the answer.

## Live results

- The deployed smoke suite passed frontend assets, security headers, health,
  prediction, ten-city analytics, anonymous protected-route rejection, and
  malformed-request validation.
- Three live what-if calls returned valid EUR estimates. The baseline was EUR
  62.07; five additional amenities returned EUR 69.80, one additional guest
  returned EUR 67.69, and superhost status returned EUR 62.47. These values are
  model outputs for the tested scenario and are not guaranteed prices.
- The isolated integration test inserted one disposable user-scoped DynamoDB
  record. Claude Haiku returned the stored Paris location, EUR 123.45 estimate,
  and 17-amenity value. Response metadata reported one saved prediction used,
  CloudWatch telemetry reported one history record, and cleanup deleted the row.
- Prediction image `1.0.6` completed ECR scanning with zero HIGH or CRITICAL
  findings. Six MEDIUM and one LOW findings remain for later dependency review.
- Direct frontend S3 access returned HTTP 403. A WAF script probe returned HTTP
  403. All five CloudWatch alarms reported `OK`.
- The operator email subscription was confirmed. No artificial alarm transition
  was triggered during this review.
- The final Terraform plan reported no changes.

## Post-review cleanup

On 4 October 2026, the development application stack was destroyed through
Terraform after a reviewed plan reported `0 to add, 0 to change, 125 to
destroy`. The resulting application state was empty, and direct AWS checks found
no remaining project Lambda functions, VPC, ECR repository, CloudWatch alarms,
SNS topic, CloudFront distribution, or WAF web ACL. The encrypted Terraform
backend bucket and KMS key were intentionally retained for future redeployment.

## Remaining limits

The supplied data is a cross-sectional listing snapshot. The application can
estimate and compare listing configurations but cannot forecast future prices,
demand, occupancy, or investment returns. A separate two-user browser isolation
journey and cross-region recovery exercise remain future work.
