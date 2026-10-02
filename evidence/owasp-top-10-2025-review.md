# OWASP Top 10:2025 Control Review

## Scope and interpretation

This review uses the current official [OWASP Top 10:2025](https://top10.owasp.org/2025/en/) awareness categories. It maps implemented controls and observed tests; it is not a penetration-test certificate or a claim that automated tools prove complete OWASP coverage. OWASP states that the Top 10 is a starting point and that tools cannot comprehensively verify every category.

| Category | Implemented controls and observed checks | Residual risk |
|---|---|---|
| A01 Broken Access Control | API Gateway JWT authorization protects saved predictions, history, and chat. Handlers derive ownership from the verified `sub` claim. Anonymous route checks returned HTTP 401; direct S3 returned HTTP 403. | A separate two-user browser isolation journey remains desirable. |
| A02 Security Misconfiguration | Terraform validation, no-drift planning, private S3 origins, restrictive CORS, CSP and security headers, WAF, private Lambda networking, and no world-open security-group rules were checked. | The generated CloudFront hostname uses the AWS default certificate policy field; a controlled domain and ACM certificate are needed for an explicitly selected modern viewer policy. |
| A03 Software Supply Chain Failures | Actions are commit-pinned; dependency audits, CodeQL, Bandit, immutable ECR tags, scan-on-push, and a pinned ZAP image are used. The retest found two HIGH base-image findings in `1.0.4`; `1.0.5` updated curl/libcurl and scanned with zero HIGH or CRITICAL findings. | Continue scanning every rebuilt image and reviewing transitive packages. |
| A04 Cryptographic Failures | HTTPS, HSTS, S3 encryption, DynamoDB encryption, KMS-encrypted SNS, encrypted Athena output, and an encrypted Terraform backend are used. No credentials are stored in source. | A custom ACM certificate requires a team-controlled domain and DNS validation. |
| A05 Injection | Strict JSON schema validation rejects unknown and invalid fields; clients cannot submit Athena SQL; output is rendered through safe DOM properties; CSP restricts scripts. WAF blocked XSS and LFI signatures, and ZAP reported zero enforced warnings. | Passive DAST is not a substitute for an authenticated manual penetration test. |
| A06 Insecure Design | Threat mapping, user-scoped records, separate Lambda roles, bounded chat context/output, route throttles, idempotency, two-AZ subnets, and private endpoints reduce blast radius. | Cross-region recovery and multi-user isolation are not implemented tests. |
| A07 Authentication Failures | Cognito email verification, strong password policy, authorization code with PKCE, OAuth state validation, token revocation, TOTP MFA, and API JWT validation are configured. | The browser session still depends on frontend script integrity; no external identity federation is required for this scope. |
| A08 Software or Data Integrity Failures | Terraform, immutable image tags, image digests, pinned workflow actions, model pipeline reuse, idempotency fingerprints, CloudTrail validation, and reviewed plans protect integrity. | The project does not implement artifact signing or SLSA provenance. |
| A09 Security Logging and Alerting Failures | Structured CloudWatch logs, five alarms, a dashboard, encrypted SNS, WAF metrics, and CloudTrail are configured. All alarms were `OK` after testing. | The SNS email subscription created during the final rebuild was pending confirmation before teardown. |
| A10 Mishandling of Exceptional Conditions | Handlers return bounded safe JSON errors without traces; tests cover malformed JSON, missing fields, dependency failure, malformed model output, and unavailable history. API throttling rejects excess load with HTTP 429 rather than backend failure. | Chaos testing remains bounded and does not prove every managed-service failure mode. |

## Dynamic and load observations

- The pinned OWASP ZAP baseline crawled 175 URLs and reported 0 failures, 0 warnings, 63 passed rules, and 4 reviewed ignores before the WAF response correction.
- CloudFront originally converted WAF HTTP 403 responses to the SPA page with HTTP 200. The unnecessary 403 rewrite was removed, a regression test was added, and the same XSS signature then returned HTTP 403 while WAF sampled requests recorded `BLOCK`.
- The post-fix ZAP baseline again returned exit code 0 with 0 failures and 0 warnings. Its crawl was smaller because blocked and missing paths now retain HTTP 403 instead of being rewritten as the home page.
- JMeter served 238 CloudFront requests with 0 failures. The paced health profile served 19 requests with 0 failures. A bounded 100-request burst produced 57 HTTP 200 and 43 expected HTTP 429 responses, with no Lambda errors.
