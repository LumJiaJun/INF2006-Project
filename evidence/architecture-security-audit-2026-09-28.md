# Architecture and Security Audit - 2026-09-28

## Scope

This review covered the Terraform configuration, Python Lambda code, frontend JavaScript, dependency files, authentication boundaries, storage controls, and GitHub Actions workflows on the `nixon` branch.

Security cannot be proven perfect by a static review. The results below record observed controls, identified limitations, and proportionate decisions without claiming that no vulnerability exists.

## Architecture Decision

The current serverless architecture remains appropriate for the measured requirements:

- CloudFront serves a private S3 origin through Origin Access Control.
- API Gateway invokes focused Lambda functions.
- Cognito JWT authorization protects prediction history and the optional AI route.
- DynamoDB is an AWS managed regional service and does not sit inside a customer VPC.
- S3 stores frontend and data lake objects with public access blocked and encryption at rest.
- Glue and Athena provide the approved analytics path.
- CloudWatch and SNS provide logs, metrics, alarms, and notifications.

No VPC or NAT Gateway was added. The Lambda functions currently use managed AWS services and public AWS service endpoints, and no private subnet resource requires VPC connectivity. Adding a VPC now would add NAT cost, cold-start/network complexity, and new failure modes without creating a meaningful data boundary around DynamoDB. If a future Lambda must enter a VPC, gateway endpoints for S3 and DynamoDB should be preferred before a NAT Gateway.

No WAF was added. API throttling, input validation, restricted CORS, JWT authorization, and CloudFront security headers address the current low-volume academic workload. WAF should be reconsidered only if deployment evidence shows an internet threat or abuse pattern that justifies its recurring cost.

No custom ACM certificate or Route 53 zone was added. CloudFront already provides HTTPS using its managed `cloudfront.net` certificate. A custom certificate would require an owned domain and ACM in `us-east-1`. The default CloudFront certificate does not allow Terraform to set a stricter minimum TLS policy, so this remains a documented limitation rather than an invented domain dependency.

## Zero Trust Review

- Validate explicitly: Cognito JWT claims authorize protected routes, backend schemas validate requests, and Athena queries are fixed application queries rather than caller-supplied SQL.
- Use least privilege: Lambda roles are purpose-specific and policies scope actions to the required tables, buckets, log groups, models, or Bedrock model.
- Assume breach: structured API access logs, Lambda logs, metrics, alarms, and SNS notifications support investigation without logging request bodies, JWTs, or identities.
- Protect data: S3 public access blocks, CloudFront OAC, DynamoDB point-in-time recovery, encryption at rest, HTTPS redirects, HSTS, CSP, and explicit S3 insecure-transport denies reduce exposure.
- Scope identity: prediction history derives the owner from the verified JWT `sub` claim and never accepts a caller-provided user identifier.

## Changes From This Audit

1. Added JSON API Gateway access logs with request ID, route, status, response length, and integration error only.
2. Added explicit `aws:SecureTransport` deny policies to the frontend and data lake buckets.
3. Added automatic cleanup for incomplete data lake multipart uploads after seven days.
4. Added a live, text-only estimator snapshot that updates through safe DOM `textContent` operations.

## Security Scan Results

Commands were run locally on 2026-09-28:

```text
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
bandit -r src/backend
pip-audit -r tests/requirements.txt
checkov -d src/infrastructure --framework terraform --compact --quiet
```

Observed results:

- Terraform formatting and validation passed.
- Bandit completed with no findings.
- `pip-audit` reported no known vulnerabilities in `tests/requirements.txt`.
- Checkov reported 314 passed and 72 failed checks after hardening, compared with 299 passed and 72 failed before hardening.
- The targeted API access logging, S3 HTTPS enforcement, and incomplete multipart upload checks no longer appeared as failures.

The remaining Checkov failures are not all exploitable vulnerabilities. They include broad enterprise baselines such as one-year retention for every log group, customer-managed KMS keys on every log and data store, VPC placement for every Lambda, WAF, CloudFront origin failover, cross-region S3 replication, X-Ray, Lambda code signing, reserved concurrency, and dead-letter queues for synchronous functions. These controls should be added only when risk, recovery objectives, or measured workload requirements justify their cost and complexity.

## Residual Risks and Follow-Up

- The application stack is intentionally offline, so DAST has not run against a live target. The gated ZAP workflow is ready for the next approved deployment.
- GitHub deployment requires the repository OIDC role and protected environment variables to be configured outside source control.
- CloudFront access logging is not enabled. API and Lambda logs cover application requests, while CloudFront logging should be reconsidered if edge-level investigation becomes a requirement.
- Fourteen-day log retention is a cost-conscious academic setting, not a long-term compliance retention policy.
- The CloudFront default certificate provides HTTPS but cannot enforce a custom TLS minimum policy without a custom domain and ACM certificate.
- Static analysis reduces risk but does not replace authorization tests, DAST, load tests, dependency monitoring, or review after each architecture change.

## Adheesh Branch Decision

The `origin/adheesh` branch was reviewed separately. Its StaySphere booking brand, FastAPI/RDS/container runtime, and synthetic application behavior do not match the approved serverless pricing platform or its dataset-backed claims. Those components were not merged. Only the general interaction idea of summarizing a configured listing was adapted into the existing estimator, using the current project brand and real model inputs.
