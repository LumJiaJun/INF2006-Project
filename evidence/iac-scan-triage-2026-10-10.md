# Terraform Static Scan and Triage - 2026-10-10

Tool: Checkov 3.3.26, `checkov -d src/infrastructure --framework terraform`.
Result: 393 checks passed and 84 failed (38 distinct checks). Nothing was
changed or deployed because of this scan. A report-only copy of the same scan now
runs in `.github/workflows/security.yml` (job `terraform-static`, soft fail,
version pinned); it does not block merges.

This is a generic baseline scanner, not a statement that the stack is secure or
insecure. Each finding below was reviewed against what the project actually
configures and why. "Accepted" means a deliberate cost, scope or design choice,
not that the control is irrelevant in a larger production system.

| Theme | Checks (failures) | Disposition and reason |
|-------|-------------------|------------------------|
| Log retention and log-group KMS | CKV_AWS_338 (6), CKV_AWS_158 (6) | Accepted. Log groups keep 14 days to control cost. Lambda logging excludes prompts and user records; log data is encrypted at rest by CloudWatch's default. A longer retention or a customer key would add cost. |
| Lambda hardening | CKV_AWS_272 (5), CKV_AWS_116 (5), CKV_AWS_115 (5), CKV_AWS_50 (5), CKV_AWS_173 (4) | Accepted. Code signing, X-Ray, a dead-letter queue (relevant only to asynchronous invokes; all invokes here are synchronous API calls), per-function reserved concurrency, and a customer key for environment variables are optional for this workload. Environment variables hold table and model names only, no secrets. |
| S3 depth | CKV_AWS_144 (4), CKV_AWS_18 (4), CKV2_AWS_62 (4), CKV_AWS_145 (3), CKV2_AWS_61 (2), CKV_AWS_300 (1) | Accepted, with one possible improvement. Single-Region by design (no cross-Region replication), and access logging and notifications are not needed for the demo. Buckets use encryption at rest and public-access blocks; some use S3-managed rather than customer-managed keys. Possible improvement: add lifecycle rules where flagged. |
| API Gateway authorization | CKV_AWS_309 (3) | Intentional. `GET /health`, `POST /predict` and `GET /analytics` are public by requirement. `POST /predictions`, `GET /history` and `POST /chat` use the Cognito JWT authorizer. |
| DynamoDB | CKV_AWS_119 (2), CKV_AWS_28 (1) | Accepted. Tables use server-side encryption with a KMS key but the check expects a customer-managed key. Point-in-time recovery is off only on the idempotency table because its records expire after 24 hours; it is on for the history table and a restore was tested on 2026-10-09 (`live-stack-test-2026-10-09.md`). |
| IAM | CKV_AWS_356 (2), CKV_AWS_111 (2), CKV_AWS_109 (1), CKV2_AWS_64 (1) | Accepted. The wildcard resources are the EC2 network-interface actions that Lambda in a VPC requires and the standard account-administration statement in KMS key policies. Workload roles are otherwise scoped to named resources. |
| CloudFront and WAF | CKV_AWS_174 (1), CKV2_AWS_42 (1), CKV_AWS_86 (1), CKV_AWS_310 (1), CKV_AWS_374 (1), CKV_AWS_259 (1), CKV_AWS_192 (1), CKV2_AWS_47 (1), CKV2_AWS_31 (1) | Accepted, honest limitation. The site uses the default `*.cloudfront.net` certificate, so a minimum TLS version cannot be set without a custom domain and certificate (not purchased). Access and WAF logging, origin failover and geo restriction add cost for a single-origin demo. The WAF uses AWS managed rule groups; the Log4j-specific check was not investigated further. The HSTS header is configured with a one-year max-age; the specific setting the scanner wants was not investigated. |
| CloudTrail | CKV_AWS_67 (1), CKV2_AWS_10 (1), CKV_AWS_252 (1), CKV_AWS_35 (1) | Accepted. A regional management trail with validated log files writes to a protected bucket. It is not multi-Region, not sent to CloudWatch Logs or SNS, and uses S3 default encryption rather than a customer key. |
| VPC | CKV2_AWS_11 (1), CKV2_AWS_12 (1) | Possible improvement, not done. VPC flow logs would add cost and the default security group is not explicitly emptied. The Lambda and endpoint security groups are the ones in use, and there is no NAT gateway or internet gateway. |
| Other | CKV_AWS_136 (1), CKV_AWS_195 (1), CKV_AWS_394 (1) | Accepted. ECR uses default encryption, the Glue job has no separate security configuration, and the availability-zone data source is not pinned. |

## What this does and does not show

- It supports the claim that obvious misconfigurations (public buckets,
  open ingress, unencrypted stores, wildcard actions on workloads) are absent.
- It does not replace the project's own threat tests, and it is not a
  compliance certification. No finding was remediated in this pass, so the
  list above is the current known gap list.
- The most defensible items to improve first, if time allows, are VPC flow
  logs, a lifecycle rule on the flagged buckets, and a custom domain and
  certificate for TLS policy control.
