# Architecture and Security Audit - 2026-09-28

## Scope

This review covered the Terraform configuration, Python Lambda code, frontend JavaScript, dependency files, authentication boundaries, storage controls, and GitHub Actions workflows on the `nixon` branch.

Security cannot be proven perfect by a static review. The results below record observed controls, identified limitations, and proportionate decisions without claiming that no vulnerability exists.

## Architecture Decision

The current serverless architecture remains appropriate for the measured requirements:

- CloudFront serves a private S3 origin through Origin Access Control.
- API Gateway invokes focused Lambda functions.
- Cognito JWT authorization protects prediction history and the optional AI route.
- All five Lambda functions use private subnets across two AZs; S3 and DynamoDB use gateway endpoints, while Logs, Athena, and Bedrock Runtime use interface endpoints. DynamoDB remains an AWS managed regional service and does not sit inside a customer VPC.
- S3 stores frontend and data lake objects with public access blocked and encryption at rest.
- Glue and Athena provide the approved analytics path.
- CloudWatch and SNS provide logs, metrics, alarms, and notifications.

The VPC was added after architecture review as a measured network-control improvement. It uses two private subnets, a restrictive Lambda security group, S3/DynamoDB gateway endpoints, and private interface endpoints for Logs, Athena, and Bedrock Runtime. No NAT Gateway was added because no deployed Lambda requires general internet egress. This does not make DynamoDB a resource inside the VPC; identity and IAM controls remain the primary Zero Trust boundary.

CloudFront WAF is now enabled with AWS IP reputation, AWS Common Rule Set, and per-IP rate-based protection. API throttling, input validation, restricted CORS, JWT authorization, and CloudFront security headers remain necessary layered controls. This does not claim DDoS certification; Shield and a separate incident response plan are not part of this project.

The CloudFront managed certificate remains active. A custom ACM certificate requires an owned domain, DNS validation, and ACM in `us-east-1`; it is not attached until the team supplies those values. The default CloudFront certificate does not allow Terraform to set a stricter minimum TLS policy, so custom ACM remains the next domain-dependent step.

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

The remaining Checkov failures are not all exploitable vulnerabilities. They include broad enterprise baselines such as one-year retention for every log group, customer-managed KMS keys on every log and data store, CloudFront origin failover, cross-region S3 replication, X-Ray, Lambda code signing, reserved concurrency, and dead-letter queues for synchronous functions. These controls should be added only when risk, recovery objectives, or measured workload requirements justify their cost and complexity. The scan predates the VPC, WAF, and CloudTrail additions and should be rerun before submission.

## Residual Risks and Follow-Up

- A local passive ZAP baseline ran on 2026-09-28. The protected variables were later configured and GitHub DAST run `36689377727` executed on 2026-09-30; it uploaded its report and failed closed on warning exit code 2. Current triage and remediation are recorded in `evidence/ci-cd.md`.
- GitHub deployment requires the repository OIDC role and protected environment variables to be configured outside source control.
- CloudFront access logging is not enabled. API and Lambda logs cover application requests, while CloudFront logging should be reconsidered if edge-level investigation becomes a requirement.
- Fourteen-day log retention is a cost-conscious academic setting, not a long-term compliance retention policy.
- The CloudFront default certificate provides HTTPS but cannot enforce a custom TLS minimum policy without a custom domain and ACM certificate.
- Static analysis reduces risk but does not replace authorization tests, DAST, load tests, dependency monitoring, or review after each architecture change.

## Official AWS pattern cross-check

The AWS reference comparison is recorded in
`evidence/aws-serverless-reference-review-2026-09-28.md`. It confirms that the
current Cognito, API Gateway, focused Lambda, private-subnet, DynamoDB,
CloudFront, and S3 pattern is aligned with the reviewed AWS serverless samples.
The VPC is implemented as an additional network-control boundary, not as a
claim that DynamoDB itself is inside the VPC.
