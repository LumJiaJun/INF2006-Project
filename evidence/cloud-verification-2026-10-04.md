# Redacted cloud verification

- **Objective:** Reproduce the deployed functional and control checks without recording account IDs, resource IDs, URLs, email addresses, tokens, or credentials.
- **Setup:** Authorized AWS credentials, initialized Terraform working directory, and the Terraform-managed development stack in `ap-southeast-1`.
- **Command:** `./tests/verify_cloud.ps1 -EvidencePath "evidence/cloud-verification-2026-10-04.md" -IConfirmAuthorizedTarget`
- **Expected result:** Terraform reports no drift; the public workflow passes; all Lambdas are active in two private subnets; alarms are OK; CloudTrail is logging; DynamoDB recovery is enabled; the latest Glue run succeeded; both S3 buckets block public access; and WAF remains attached to CloudFront.
- **Actual result:** Passed on 2026-10-04. Terraform managed 147 resources and returned detailed exit code 0.

## Functional workflow

  - Health check passed.
  - Frontend asset checks passed.
  - Frontend security header checks passed.
  - Prediction passed: 65.98 EUR.
  - Analytics passed: 10 city summaries.
  - Protected route authentication checks passed.
  - Malformed request validation passed.

## Deployed control summary

  - health: state Active, update Successful, private subnet count 2
  - prediction: state Active, update Successful, private subnet count 2
  - analytics: state Active, update Successful, private subnet count 2
  - history: state Active, update Successful, private subnet count 2
  - chat: state Active, update Successful, private subnet count 2
  - CloudWatch alarms: 5 checked, all OK
  - CloudTrail: logging enabled with no latest delivery error
  - DynamoDB: continuous backups and point-in-time recovery enabled
  - Glue: latest transform run SUCCEEDED
  - S3: frontend and data-lake public access blocks fully enabled
  - CloudFront: WAF web ACL attached
  - SNS: 0 confirmed subscription(s); zero means delivery is not currently active

## Interpretation

This verifies the current single-region development deployment at the tested time. It does not prove unlimited scale, multi-region recovery, authenticated multi-user isolation, or future drift-free operation. The generated evidence intentionally excludes cloud identifiers and operator contact details.

- **Artefact paths:** `tests/verify_cloud.ps1`, `tests/smoke_api.ps1`, `src/infrastructure`, and this file.
