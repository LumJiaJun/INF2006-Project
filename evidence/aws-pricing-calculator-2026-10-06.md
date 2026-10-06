# AWS Pricing Calculator Estimate - 2026-10-06

## Objective

Estimate the current deployed architecture in Asia Pacific (Singapore) using
the real Terraform resource shape and explicit low-traffic assumptions. This
is a planning estimate in USD before tax, discounts, credits, and Free Tier. It
is not an invoice or a guarantee of future charges.

## Calculator record

- AWS Pricing Calculator workload estimate name:
  `INF2006-Airbnb-2026-10-06`
- Rate type: `BEFORE_DISCOUNTS`
- Calculator status: `VALID`
- Calculator subtotal: **USD 72.12 per month**
- Estimate expiry reported by AWS: 6 November 2027
- Detailed redacted export:
  `evidence/aws-pricing-calculator-estimate-2026-10-06.csv`

The estimate was created through the official AWS Pricing Calculator API with
`aws bcm-pricing-calculator create-workload-estimate`. Usage lines were added
with `batch-create-workload-estimate-usage` and read back with
`list-workload-estimate-usage`. The committed export removes the estimate ID,
AWS account ID, resource IDs, and operator details.

## Workload assumptions

- One continuously deployed month is 730 hours.
- Three interface endpoint services are attached in two availability zones,
  producing 6 endpoint ENIs and 4,380 endpoint-hours per month.
- WAF contains one web ACL, two AWS managed-rule statements, one rate rule,
  and 60,000 inspected requests.
- Workload volume includes 10,000 API requests, 10,000 Lambda requests,
  1,700 Lambda GB-seconds, 10 Cognito monthly active users, 1 GB of S3, ECR,
  and CloudWatch log storage, and low DynamoDB and Athena usage.
- One Glue run uses 0.05 DPU-hours, equivalent to two workers for about
  90 seconds.
- The AI scenario uses 300,000 input tokens and 100,000 output tokens through
  the global Claude Haiku 4.5 inference profile.

## Monthly result

| Group | Estimated monthly cost |
|-------|-----------------------:|
| VPC interface endpoints | $56.95 |
| WAF and KMS security controls | $10.07 |
| CloudWatch dashboard, alarms, and logs | $4.20 |
| CloudFront and ECR delivery | $0.59 |
| Cognito | $0.15 |
| Glue and Athena | $0.07 |
| S3 and DynamoDB | $0.04 |
| Lambda and API Gateway | $0.04 |
| **AWS Pricing Calculator subtotal** | **$72.12** |
| Claude Haiku 4.5 token scenario | $0.80 |
| **Planning total** | **$72.92/month** |

Claude Haiku 4.5 is billed as a third-party model. The Pricing Calculator
workload API did not resolve the Marketplace model line unambiguously, so its
token cost is calculated separately from AWS's published global-inference
rate of $1 per million input tokens and $5 per million output tokens. This
exception is shown rather than forcing an incorrect generic model price into
the calculator subtotal.

## Interpretation

The two-AZ interface endpoints account for about 78 percent of the planning
total and are the main reason the current architecture is not a $4-$7 monthly
stack. At full-month pricing, the architecture is approximately $2.40 per day.
A short 48-hour demonstration is roughly $4.70-$5.60 before tax, depending on
actual logs, AI tokens, and AWS billing treatment. Destroying the application
stack promptly is the strongest development cost control; the shared remote
state backend remains separately retained.

Gateway endpoints for S3 and DynamoDB have no endpoint-hour charge. Removing
one interface endpoint or one availability zone would reduce cost but would
weaken the documented private-service path or in-Region availability. The
current choice is therefore suitable for a short assessed deployment, not an
always-on low-budget student environment.

## Verification status

- Nixon Lee Disheng created the calculator record, checked every usage line
  against Terraform, and reconciled the total on 6 October 2026.
- The live cloud verifier passed with 148 Terraform resources and zero drift.
- Group-wide verification is **not yet claimed**. Each teammate should compare
  this file, the CSV export, and the Terraform service list before adding their
  name and date. This prevents an unsupported "group verified" statement.

## Sources

- AWS Pricing Calculator workload estimate API and AWS Price List rates,
  retrieved on 6 October 2026.
- `src/infrastructure` for the deployed service quantities.
- `evidence/cloud-verification-2026-10-06.md` for live deployment status.
- AWS WAF, PrivateLink, Bedrock, KMS, and service pricing pages linked from
  `evidence/cost-estimate.md`.
