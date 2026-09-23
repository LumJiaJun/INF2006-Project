# Threat-Control Map

Map named threats to the controls that mitigate them, with evidence links.

| Threat | Control implemented | Evidence |
|--------|---------------------|----------|
| Direct public access to frontend objects | S3 Block Public Access and a bucket policy scoped to the CloudFront distribution | `src/infrastructure/frontend.tf`, `evidence/test-security.md` |
| Public or unintended access to raw analytical data | A separate S3 data-lake bucket has Block Public Access, bucket-owner enforcement, encryption, and role-scoped object access | `src/infrastructure/data_lake.tf` |
| Arbitrary or unexpectedly expensive analytics queries | Clients can invoke only a fixed server-side query; the Athena workgroup enforces a 1 GiB scan cutoff and seven-day result expiry | `src/backend/analytics/handler.py`, `src/infrastructure/data_lake.tf` |
| Operational failures going unnoticed | CloudWatch alarms publish to an encrypted SNS topic, and a dashboard exposes API errors and Lambda duration/errors | `src/infrastructure/monitoring.tf`, `evidence/monitoring.md` |
| Over-privileged compute identity | The health Lambda role can only write to its dedicated CloudWatch log group | `src/infrastructure/api.tf` |
| Unauthorized prediction-history access | API Gateway validates Cognito JWTs, and handlers derive the DynamoDB partition key only from the verified `sub` claim | `src/infrastructure/auth.tf`, `src/backend/history/handler.py`, `evidence/test-security.md` |
| OAuth authorization-code interception or request forgery | The browser uses PKCE with SHA-256 and validates a cryptographically random state value | `src/frontend/auth.js` |
| Long-lived browser token exposure | ID tokens are held in `sessionStorage`, expire after the token lifetime, and are cleared at sign-out | `src/frontend/auth.js` |
| Unapproved browser origins calling the API | API Gateway CORS allows only the deployed CloudFront origin | `src/infrastructure/api.tf`, `evidence/test-security.md` |
| Unencrypted browser traffic | CloudFront and API Gateway expose HTTPS endpoints and CloudFront redirects HTTP requests to HTTPS | `src/infrastructure/frontend.tf` |
| Secret leakage through source control | Local environment files, Terraform state, private keys, and sensitive variable files are ignored | `.gitignore`, `src/.env.example` |

## Secrets handling

The Cognito frontend client is intentionally public and has no client secret. Terraform uses the standard AWS credential chain outside the repository, and Lambda uses IAM execution roles. No AWS access key, token, password, or private key is committed. Future secrets must use an appropriate managed service or runtime reference and must not be stored in Git.
