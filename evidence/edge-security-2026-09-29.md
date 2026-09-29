# Edge security and audit evidence - 2026-09-29

## CloudFront WAF

- A global-scope WAF web ACL was created in `us-east-1` and attached to the CloudFront distribution.
- The ACL has AWS managed Amazon IP reputation rules, AWS managed Common Rule Set rules, and a 2,000-request-per-five-minute per-IP rate rule.
- WAF sampled requests and CloudWatch metrics are enabled.
- The frontend smoke suite continued to pass after the WAF attachment, including assets, security headers, prediction, analytics, protected-route rejection, and malformed-input validation.
- This is application-edge protection, not DDoS certification. AWS Shield and a separate response plan remain outside this academic deployment.

## Scoped CloudTrail

- A regional management-event trail was created in `ap-southeast-1`.
- The trail records management read/write events, excludes data-event logging to control volume, validates log files, and delivers to a dedicated encrypted, versioned, public-access-blocked S3 bucket.
- The S3 bucket expires audit objects after 90 days and permits writes only from the named CloudTrail trail through the service principal, account condition, source-trail ARN, and exact `management/AWSLogs/` prefix.
- `get-trail-status` reported logging enabled, and the trail configuration reported single-region operation and log-file validation enabled.

## ACM status

The CloudFront generated domain and AWS-managed CloudFront certificate remain active. A custom ACM certificate cannot be issued or attached until the team supplies a domain it controls and completes DNS validation. The certificate must be in `us-east-1` for CloudFront; no fabricated domain or unvalidated certificate is deployed.
