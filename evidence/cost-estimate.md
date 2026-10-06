# Monthly Cost Estimate

**Estimate date:** 2026-10-06

**Region:** Asia Pacific (Singapore)

**Currency:** USD before tax

**Purpose:** Compare the deployed serverless design with EC2 hosting at low project traffic. This is an estimate, not a bill or quotation.

## Assumptions

- 10,000 page journeys and 10,000 non-AI API requests per month.
- 1,000 authenticated AI questions per month.
- Each AI question averages 300 input tokens and 100 output tokens.
- One 90-second Glue run per month using two `G.1X` workers.
- About 5 GB of monthly internet delivery, less than 1 GB of application storage, and low log volume.
- Free-tier credits are excluded from the main comparison because account eligibility varies.

## Current deployed estimate

An official AWS Pricing Calculator workload estimate named
`INF2006-Airbnb-2026-10-06` was created through the
`bcm-pricing-calculator` API and returned a valid before-discounts subtotal of
**$72.12 per continuously deployed month**. Adding the separately calculated
global Claude Haiku 4.5 token scenario produces a planning total of
**$72.92/month** before tax, credits, discounts, and Free Tier.

| Component group | Monthly estimate | Basis |
|---|---:|---|
| VPC interface endpoints | $56.95 | Three interface endpoint services in two AZs: 4,380 endpoint-hours plus 1 GB processed |
| WAF and KMS | $10.07 | One web ACL, three rules, 60,000 requests, two keys, and 10,000 KMS requests |
| CloudWatch | $4.20 | One dashboard, five alarms, and 1 GB logs |
| CloudFront and ECR | $0.59 | 5 GB delivery, 60,000 HTTPS requests, and 1 GB image storage |
| Cognito | $0.15 | 10 monthly active users at the calculator's before-discounts rate |
| Glue and Athena | $0.07 | 0.05 DPU-hours and 0.01 TB scanned |
| S3, DynamoDB, Lambda, and API Gateway | $0.09 | Low storage, request, and compute volume |
| AWS Pricing Calculator subtotal | **$72.12** | Saved valid workload estimate |
| Claude Haiku 4.5 | $0.80 | 0.3M global input tokens at $1/M and 0.1M output tokens at $5/M |
| **Planning total** | **$72.92/month** | About **$2.40/day** while continuously deployed |

The redacted calculator line items, assumptions, expiry, and verification
status are in `evidence/aws-pricing-calculator-2026-10-06.md` and
`evidence/aws-pricing-calculator-estimate-2026-10-06.csv`. The calculator
workload API could not unambiguously map the third-party Marketplace model
line, so Bedrock is shown separately rather than assigned an incorrect generic
foundation-model rate.

## Historical pre-VPC serverless baseline

The table below is retained as design-history evidence. It predates the
two-AZ interface endpoints, WAF, and CloudWatch dashboard and is **not** the
current full-architecture estimate.

| Component | Monthly estimate | Basis |
|---|---:|---|
| Claude Haiku 4.5 | $0.80 | 0.3M global input tokens at $1/M plus 0.1M output tokens at $5/M |
| KMS customer-managed keys | $2.00 | One operational-alert key and one shared-state key |
| Glue ETL | $0.02 | Two DPUs for about 1.5 minutes at $0.44/DPU-hour |
| CloudFront, S3 and ECR | $0.75 | Small static site, about 5 GB delivery, and one prediction image |
| API Gateway, Lambda, DynamoDB, Athena, Cognito and CloudWatch | $1.25 | Low request, compute, scan and log volume with a contingency allowance |
| **Historical estimated total** | **about $4.82/month** | Superseded by the current calculator result above |

At 10,000 AI questions with the same token shape, Bedrock rises from about
$0.80 to about $8.00, producing a historical pre-VPC total near $12/month. The
application therefore requires Cognito on `/chat`, limits messages to 500
characters, caps responses at 220 tokens, and throttles this route to one
request per second.

## Comparable EC2 baselines

AWS Price List API rates retrieved on 2026-09-24 for Singapore were: `t3.small` Linux $0.0264/hour, gp3 $0.096/GB-month, Application Load Balancer $0.0252/hour plus $0.008/LCU-hour, public IPv4 $0.005/hour, and NAT Gateway $0.059/hour plus data processing.

| Design | Monthly fixed hosting | Calculation |
|---|---:|---|
| Minimal, not highly available | **$24.84** | One `t3.small` ($19.27), 20 GB gp3 ($1.92), one public IPv4 ($3.65) |
| Two-instance web tier | **$73.92** | Two `t3.small` ($38.54), 40 GB gp3 ($3.84), ALB hours ($18.40), one average LCU ($5.84), two ALB IPv4 addresses ($7.30) |
| Private two-instance web tier | **$116.99** | Two-instance total plus one NAT Gateway hour charge ($43.07), before NAT data processing |

These EC2 figures intentionally keep Cognito, Bedrock, DynamoDB and analytical services unchanged so the comparison isolates web and API hosting. They exclude backup storage, additional NAT gateways, database replacement, traffic, monitoring growth and engineering time for patching, scaling and failover. A production multi-AZ design with one NAT Gateway per availability zone would be higher.

## Interpretation

For this low-volume, uneven university workload, the compute and data path
remain cheaper than continuously running EC2. However, the assessed private
network design has a fixed endpoint-hour floor, so it is no longer accurate to
describe the complete stack as a $4-$7 monthly deployment. Compared with the
private two-instance EC2 baseline, the current planning estimate remains about
$44/month lower while avoiding server patching and reverse-proxy operations.
Actual spend must be checked in AWS Cost Explorer after deployment.

## Pricing sources

- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)
- [Amazon EC2 On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
- [AWS Price List API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html)

## FinOps review after VPC, WAF, and CloudTrail

The original estimate predated the private Lambda VPC, CloudFront WAF, and
CloudTrail additions. The current calculator result now includes the dominant
fixed controls. The most important change is six interface endpoint
network interfaces: Logs, Athena, and Bedrock Runtime are each provisioned in
two availability zones. AWS PrivateLink charges for interface endpoints by
endpoint-hour in each AZ and also charges for data processed, so this fixed
cost can exceed the low-volume Lambda and API charges. S3 and DynamoDB gateway
endpoints do not have the same interface-endpoint hourly model. See the
[AWS PrivateLink pricing guidance](https://aws.amazon.com/privatelink/faqs/).

The WAF adds one global web ACL, two AWS managed rule groups, one rate rule,
and per-request inspection charges. AWS's current pricing page lists a base
web ACL charge, per-rule charges, and request charges; the exact monthly total
depends on CloudFront request volume. The current rules are intentionally
limited to IP reputation, Common Rule Set, and rate limiting; Bot Control,
CAPTCHA, and Fraud Control are not enabled because they would add cost without
a demonstrated requirement. See the [AWS WAF pricing page](https://aws.amazon.com/waf/pricing/).

The CloudTrail trail is scoped to one region and management events only. One
copy of ongoing management events delivered to S3 has no CloudTrail delivery
charge, but the S3 bucket still incurs storage and request charges. The 90-day
lifecycle rule prevents indefinite log accumulation. Data events, CloudTrail
Lake, Insights, CloudWatch Logs delivery, and multi-region duplication remain
disabled unless a security requirement justifies their cost. See the [AWS
CloudTrail pricing page](https://aws.amazon.com/cloudtrail/pricing/).

Public ACM certificates used with CloudFront are free; the cost concern is the
domain and DNS service, not the integrated certificate itself. A custom ACM
certificate should only be added after a real domain and DNS ownership are
available. See the [ACM pricing page](https://aws.amazon.com/certificate-manager/pricing/).

### Recommended cost controls

1. Keep the two-AZ endpoint layout for the assessed architecture; for a
   temporary development environment, make the VPC optional and destroy it
   after evidence collection rather than paying endpoint-hours overnight.
2. Keep the prediction Lambda at 2 GB until a fresh cold-start benchmark
   proves a lower memory size meets the latency target. Right-size the other
   functions from CloudWatch p95 duration and memory metrics instead of
   reducing them blindly.
3. Keep chat protected by Cognito, 500-character input validation, 220-token
   output limits, and a one-request-per-second route throttle because Bedrock
   is the variable usage cost.
4. Keep Glue manual or data-change triggered, with two `G.1X` workers, a
   ten-minute timeout, no retries, Parquet partitioning, and Athena's 1 GiB
   scan cutoff.
5. Keep CloudWatch logs at 14 days, ECR at three images, CloudTrail at 90 days,
   and CloudFront at `PriceClass_100` unless evidence requires expansion.
6. Add an AWS Budget alert and Cost Anomaly Detection in the account console,
   with a low development threshold, before long-running demonstrations.
7. Review Cost Explorer by `Project` and `Environment` tags after 24-48 hours;
   the endpoint, WAF, Bedrock, Glue, and CloudTrail line items should be
   checked separately rather than hidden in a single serverless estimate.

## Verification statement

Nixon Lee Disheng created and reconciled the saved calculator workload estimate
against Terraform on 6 October 2026. Group-wide verification is pending and is
not claimed until the other members review the redacted line items and record
their names and dates.
