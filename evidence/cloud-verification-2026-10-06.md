# Live Cloud Verification - 2026-10-06

## Objective

Recreate the assessed AWS stack from the retained encrypted Terraform backend,
load the real dataset, and verify the live functional and security controls
without committing cloud identifiers, URLs, email addresses, tokens, state, or
credentials.

## Deployment method

1. AWS identity and remote state access were confirmed.
2. The full-data training replay matched the committed dataset hash, split,
   candidate metrics, selected model, model hash, and model size exactly.
3. A targeted ECR bootstrap plan contained 1 create, 0 changes, and 0 destroys.
4. The immutable prediction image was built for Linux AMD64 and pushed under
   tag `d7fb1bdd1c61`.
5. The reviewed full Terraform plan contained 124 creates, 0 changes, and
   0 destroys.
6. After apply, a second plan with the same image and alert configuration
   returned `No changes`.
7. The real listing CSV was uploaded through the private data-lake path and
   the Glue transformation completed with `SUCCEEDED`.

## Actual result

- Terraform manages 148 resources with zero detected drift.
- Frontend, security headers, health, prediction, analytics, authentication
  rejection, and malformed-input smoke checks passed.
- The prediction smoke scenario returned 65.98 EUR.
- Analytics returned all 10 city summaries.
- All five Lambda functions are active, have successful update status, and are
  configured with both private subnets.
- All five CloudWatch alarms were `OK`.
- CloudTrail logging was enabled without a latest delivery error.
- DynamoDB continuous backups and point-in-time recovery were enabled.
- Both S3 use cases retained all Block Public Access settings.
- CloudFront retained the WAF web ACL.
- The ECR scan completed with 0 CRITICAL, 0 HIGH, 6 MEDIUM, and 1 LOW finding.
  The remaining findings require dependency review; no zero-vulnerability
  claim is made.
- A direct live chat Lambda invocation with verified claims returned HTTP 200,
  a bounded Claude Haiku 4.5 answer, and used zero saved history records for
  the synthetic verification subject.
- The SNS email subscription was created but remained `PendingConfirmation`.
  Alarm email delivery is not active until the operator confirms the new
  subscription email.

## Commands

```powershell
python tests/verify_full_model.py --listings "data/raw/Airbnb Data/Listings.csv"
terraform -chdir=src/infrastructure plan -var="prediction_image_tag=<immutable-tag>"
terraform -chdir=src/infrastructure apply <reviewed-plan>
./tests/verify_cloud.ps1 -AlertEmail "<operator-email>" -IConfirmAuthorizedTarget
```

## Interpretation

This proves the dated single-account deployment and control checks. It does
not prove unlimited scale, zero vulnerabilities, cross-Region failover,
multi-user browser isolation, future drift-free operation, or confirmed email
delivery. The public frontend URL is obtained from
`terraform -chdir=src/infrastructure output -raw frontend_url` rather than
stored in evidence.

- **Artefact paths:** `tests/verify_cloud.ps1`, `tests/smoke_api.ps1`,
  `src/infrastructure`, `evidence/aws-pricing-calculator-2026-10-06.md`, and
  this file.
