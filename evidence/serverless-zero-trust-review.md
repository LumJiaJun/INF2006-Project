# Serverless Applications Lens and Zero Trust review

Date: 2026-09-28

This review compares the deployed architecture with the supplied AWS Serverless Applications Lens and Zero Trust guidance. It records implemented decisions, evidence, and remaining gaps. It does not claim formal AWS Well-Architected certification.

## Serverless workload review

| Area | Implemented design | Evidence and remaining gap |
|------|--------------------|----------------------------|
| Compute | Five focused Lambda functions provide health, prediction, history, analytics, and protected AI. Functions keep durable state in managed services. Warm-container globals cache only SDK clients or the read-only model bundle. | `src/backend/`; 25 unit tests. Strict idempotency is not implemented for repeated authenticated prediction submissions, so a retry after an uncertain response can create another history item. The browser disables duplicate submission while a request is active, but that is not a complete idempotency control. |
| Data | Static assets, application records, and analytical data use separate S3 and DynamoDB resources. DynamoDB uses on-demand capacity and a user/time access pattern. Glue writes city-partitioned Parquet queried through Athena. | `src/infrastructure/frontend.tf`, `data.tf`, `data_lake.tf`; `evidence/data-pipeline.md`. The prediction model is isolated in an immutable ECR image rather than the data-lake model prefix. |
| Identity | Cognito handles application users with required TOTP authenticator-app MFA. API Gateway validates JWTs for history, saved predictions, and AI access. History ownership comes only from the verified `sub` claim. AWS services use separate IAM roles. | `src/infrastructure/auth.tf`; `tests/test_history.py`; `tests/test_chat.py`; `evidence/test-security.md`. The authenticated browser journey verified the protected flow; no credentials or MFA codes are stored in evidence. |
| Edge | CloudFront is the frontend entry point and uses a private OAC S3 origin. The response policy adds CSP, HSTS, anti-framing, MIME-sniffing protection, and a strict referrer policy. | `src/infrastructure/frontend.tf`; live smoke security-header test. WAF is not added because no demonstrated threat justifies its cost and rule operations for this project. |
| Monitoring | Structured logs, detailed API metrics, Lambda invocation/error/duration/throttle metrics, a dashboard, five alarms, and an encrypted SNS action topic are provisioned. AI duration and errors have their own series. | `src/infrastructure/monitoring.tf`; `evidence/monitoring.md`. The topic requires an operator-managed confirmed subscriber. |
| Deployment | Terraform controls cloud resources. Plans are reviewed before apply. ECR tags are immutable, shared state uses a versioned S3 backend with KMS encryption and lockfiles, and GitHub Actions validates every change. Raw-data upload and Glue execution remain controlled data operations. | `src/infrastructure/README.md`, `src/infrastructure/bootstrap`, `.github/workflows`; Git history. The AWS deployment role and GitHub environment variables must be configured before CD can run. |
| Release management | Immutable prediction images and Git/Terraform rollback provide basic release recovery. | `src/infrastructure/ecr.tf`. Lambda versions, aliases, and canary deployment are not added because the current single development environment has not demonstrated a need. |
| Messaging | SNS is used only for operational notifications. Prediction remains a direct synchronous API-to-Lambda workflow. | `src/infrastructure/monitoring.tf`. SQS, EventBridge, and Step Functions are intentionally absent because there is no multi-step asynchronous workflow. |

## Performance, cost, and failure design

- Prediction memory was increased from 1 GB to 2 GB only after a measured cold-start improvement from 13.8 seconds to approximately 3.0 to 3.3 seconds. Warm observations were 59 to 70 ms.
- The expected-load health test accepts successful `200` and controlled `429` responses. The stress test honestly records `503` responses caused by the account concurrency quota of 10.
- Athena reads processed Parquet, not the raw CSV. The recorded aggregate scanned 566,077 bytes and completed in 697 ms.
- DynamoDB uses on-demand billing because the workload is low and unpredictable. Glue runs with two `G.1X` workers, a ten-minute timeout, and no retries.
- Bedrock runs through a separate Lambda and protected route. Prompts are limited to 500 characters, responses to 220 tokens, and route throughput to one request per second.
- Malformed input, unsupported categories, missing claims, Athena failure, model failure, and DynamoDB failure return controlled responses without stack traces. Downstream failures are logged.
- Automatic retries are not added to synchronous write paths because blind retries could create duplicate history records. A future idempotency-key design should precede any client retry policy.

## Zero Trust interaction map

| Interaction | Explicit trust and authorization control |
|-------------|------------------------------------------|
| Browser to CloudFront | HTTPS and CloudFront response security headers |
| CloudFront to frontend S3 | Origin Access Control plus a bucket policy restricted to the distribution ARN |
| Browser to protected API | Cognito authorization-code flow with PKCE, API Gateway JWT validation, and backend claim-derived identity |
| API Gateway to Lambda | Per-route `aws_lambda_permission` source ARN |
| Prediction Lambda to DynamoDB | Dedicated role with `dynamodb:PutItem` on one table |
| History Lambda to DynamoDB | Dedicated role with `dynamodb:Query` on one table; no `Scan` |
| Chat Lambda to Bedrock and DynamoDB | Cognito-protected route; dedicated role can invoke the selected Haiku model and query only the prediction-history table using the verified subject partition key |
| Analytics Lambda to Athena, Glue, and S3 | Dedicated role restricted to one workgroup, catalog objects, processed prefix, and result prefix |
| Glue to S3 | Dedicated role restricted to the script, raw listing prefix, and processed listing prefix |
| CloudWatch alarms to SNS | Named alarms publish through a customer-managed KMS key scoped by source account and alarm ARN |

## Zero Trust test results

- Anonymous frontend and data-lake S3 object requests returned HTTP 403.
- Unauthenticated `GET /history`, `POST /predictions`, and `POST /chat` returned HTTP 401.
- Unit tests confirmed the history partition key comes from verified JWT claims.
- Malformed prediction JSON returned HTTP 400 with a safe error.
- CloudFront responses included CSP, HSTS, `X-Content-Type-Options`, and `X-Frame-Options`.
- IAM simulation returned `allowed` for prediction `dynamodb:PutItem`, history `dynamodb:Query`, and Glue access to `raw/listings/`.
- IAM simulation returned `implicitDeny` for prediction access to raw S3 data, history `dynamodb:Scan`, and Glue access to `raw/reviews/`.
- Alarm history recorded successful publication to the encrypted SNS topic after the KMS policy was corrected.

## Decisions not to add services

- **AWS WAF:** No observed attack pattern or public scale requirement justifies rule cost and maintenance. API validation, JWT authorization, CORS, CSP, and throttling address the currently tested threats.
- **ACM custom certificate and Route 53:** CloudFront's generated domain already has managed HTTPS. A custom certificate requires a domain and DNS validation, neither of which is a current project requirement.
- **CloudTrail trail:** Account-level API auditing is valuable for a longer-lived shared environment, but creating a project trail adds another bucket, retention decisions, and account-level operational ownership. Git, Terraform, CloudWatch application logs, and alarm history cover current submission traceability. This is an acknowledged audit gap, not a claim that CloudTrail is unnecessary generally.
- **VPC and NAT Gateway:** The functions use public AWS service endpoints and hold no private network resource. Adding a VPC would add cold-start, routing, and cost complexity without creating an identity boundary.
- **Step Functions, SQS, and EventBridge:** The current workflows are short and synchronous. No demonstrated orchestration or buffering requirement exists.
- **Customer-managed keys for every store:** Application S3 and DynamoDB use managed at-rest encryption. Customer-managed keys are limited to SNS and Terraform state, where alarm-policy and shared-state requirements justify the added cost and lifecycle.

## Priority follow-up work

1. Add a confirmed SNS operator endpoint outside source control.
2. Configure the GitHub OIDC deployment role and protected environment variables.
3. Design server-side idempotency before adding retries to saved predictions.
4. Request a suitable Lambda concurrency quota and repeat the stress test.
5. Keep required Cognito TOTP MFA enabled and retest it after authentication changes.
6. Re-evaluate CloudTrail when the account becomes shared or long-lived.
