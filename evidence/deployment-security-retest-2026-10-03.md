# Deployment and Security Retest - 3 October 2026

## Deployment

- Terraform recreated the encrypted immutable ECR repository first so the required Lambda image could exist before the full graph was applied.
- Image `1.0.4` was built and pushed, then the reviewed full plan applied 123 additional resources. Across both stages, Terraform added 125 resources with no changes or destruction.
- The real listings CSV was uploaded to the private data lake. Glue run `jr_a95124e47b8dd6c67056df55bf9edbce5966ec24afeb43d8cb33390ca69f8369` succeeded and produced the governed analytical data.

## Functional and security results

- The final local preflight passed 38 tests, Python compilation, five JavaScript syntax checks, Terraform formatting/validation, synthetic model training, and loopback HTTP checks.
- The deployed smoke journey passed frontend assets and headers, health, prediction, ten-city analytics, anonymous JWT rejection, and malformed-request validation.
- The chat integration inserted one synthetic user-scoped record, confirmed the deployed Lambda retrieved exactly that record for Bedrock context, received a bounded reply, and removed the record.
- Bandit, two pinned dependency audits, and Actionlint passed.
- Direct S3 access returned HTTP 403. History PITR, idempotency TTL, five available VPC endpoints, two-subnet placement for all five Lambdas, CloudTrail logging, five alarms, CORS restriction, and no world-open security-group ingress/egress were verified.
- The first pinned ZAP baseline crawled 175 URLs with zero failures and zero warnings.
- JMeter completed 238 CloudFront requests and 19 paced API requests with zero failures. A bounded burst returned only HTTP 200 and controlled HTTP 429 responses.
- Lambda metrics recorded 83 health, 2 prediction, and 1 analytics invocation with zero errors. All five alarms were `OK` after the test window.

## Defects found and corrected

1. CloudFront's SPA fallback rewrote WAF HTTP 403 responses to `index.html` with HTTP 200. The 403 rewrite was removed, a regression test was added, and the same XSS signature then returned HTTP 403.
2. ECR found two HIGH instances of CVE-2026-80230 in curl/libcurl from image `1.0.4`. The Docker build now updates those base packages. Immutable image `1.0.5` scanned with zero HIGH and zero CRITICAL findings and passed live prediction testing.
3. Versioned frontend and CloudTrail buckets were configured with `force_destroy` for repeatable development teardown. The final CloudTrail versions still required one explicit cleanup because the resource's pre-existing state had not yet recorded that setting before destroy mode.

## Teardown

- The reviewed destroy plan contained 125 deletions, 0 additions, and 0 changes.
- After the interrupted process completed, only the CloudTrail bucket and random suffix remained. CloudTrail object versions were removed from the exact project bucket and a fresh two-resource plan completed successfully.
- Terraform state and direct Lambda, VPC, CloudFront, API Gateway, DynamoDB, ECR, S3, Cognito, and WAF inventories all returned zero project application resources.
- The separate encrypted Terraform backend was verified and retained.

## Residual limitations

- The CloudFront-generated hostname uses the AWS default certificate. An explicit modern CloudFront viewer TLS policy requires a team-controlled domain and validated ACM certificate in `us-east-1`.
- The final SNS email subscription was pending confirmation before teardown, so no new delivery test was claimed.
- No test can prove that a website has no vulnerabilities. The results establish the stated controls and observed behavior within the bounded test scope.
