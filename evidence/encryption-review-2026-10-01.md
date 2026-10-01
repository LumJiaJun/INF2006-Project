# Encryption and Sensitive Data Review - 2026-10-01

## Objective

Verify that sensitive application and infrastructure information is protected in transit, at rest, in logs, and through access control. This does not claim that every harmless value is individually encrypted. Encryption complements authentication, authorization, public-access blocking, and data minimisation.

## Live verification

The following checks were run against the deployed development environment. Account identifiers, bucket names, table names, key identifiers, user identifiers, and URLs are omitted.

| Store or path | Observed encryption | Access or recovery observation |
|---|---|---|
| Private frontend S3 bucket | SSE-S3 (`AES256`) | All four S3 Block Public Access settings were `true`; CloudFront uses Origin Access Control |
| Private data-lake S3 bucket | SSE-S3 (`AES256`) | All four S3 Block Public Access settings were `true`; anonymous object access is denied |
| Private CloudTrail S3 bucket | SSE-S3 (`AES256`) | All four S3 Block Public Access settings were `true`; log-file validation is enabled |
| Terraform state S3 bucket | Customer-managed AWS KMS key (`aws:kms`) | All four S3 Block Public Access settings were `true`; versioning and native lockfiles protect shared state |
| Prediction-history DynamoDB table | Server-side encryption reported `ENABLED`, type `KMS` | Point-in-time recovery reported `ENABLED`; access is partitioned by the verified Cognito subject |
| Prediction-idempotency DynamoDB table | Server-side encryption reported `ENABLED`, type `KMS` | Records expire through a 24-hour TTL; PITR is intentionally not enabled for this short-lived retry-control data |
| Browser to CloudFront and API Gateway | HTTPS | CloudFront redirects HTTP to HTTPS; API endpoints are HTTPS; HSTS is added at the edge |
| Cognito credentials | Cognito-managed | The application receives tokens through authorization code plus PKCE and never receives or stores passwords |

## Logging review

Source inspection confirmed that prediction logs contain operational metadata and model version rather than listing inputs. Chat logs contain request ID, current page, history-record count, and token counts rather than the question, response, token, or prediction records. API responses use safe error messages without stack traces.

CloudWatch log retention is 14 days. Evidence and screenshots must continue to exclude account IDs, email addresses, Cognito subjects, tokens, credentials, exact private configuration, and token-bearing URLs.

## Browser-local decision support

Listing drafts and comparison scenarios are stored only in the user's browser and are not sent to DynamoDB. Comparison records deliberately omit account identifiers and exact coordinates. Browser storage is not presented as encrypted storage, so the interface provides clear and remove controls and must not be used for secrets or personal data.

## Commands

```powershell
aws s3api get-bucket-encryption --bucket <redacted-bucket>
aws s3api get-public-access-block --bucket <redacted-bucket>
aws dynamodb describe-table --table-name <redacted-table>
aws dynamodb describe-continuous-backups --table-name <redacted-table>
```

## Conclusion

The deployed controls protect sensitive data in transit and at rest while limiting readable exposure through IAM, Cognito, S3 policies, private networking, log minimisation, and evidence redaction. Client-side display values and non-sensitive aggregate analytics necessarily remain readable to the user who requested them.
