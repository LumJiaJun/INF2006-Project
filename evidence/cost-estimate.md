# Monthly Cost Estimate

**Estimate date:** 2026-09-24

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

## Serverless estimate

| Component | Monthly estimate | Basis |
|---|---:|---|
| Claude Haiku 4.5 | $0.88 | 0.3M input tokens at $1.10/M plus 0.1M output tokens at $5.50/M |
| KMS customer-managed key | $1.00 | One operational-alert key |
| Glue ETL | $0.02 | Two DPUs for about 1.5 minutes at $0.44/DPU-hour |
| CloudFront, S3 and ECR | $0.75 | Small static site, about 5 GB delivery, and one prediction image |
| API Gateway, Lambda, DynamoDB, Athena, Cognito and CloudWatch | $1.25 | Low request, compute, scan and log volume with a contingency allowance |
| **Estimated total** | **about $3.90/month** | Reasonable range: **$3 to $6/month** at these assumptions |

At 10,000 AI questions with the same token shape, Bedrock rises from about $0.88 to about $8.80, producing an estimated serverless total near $12/month. The application therefore requires Cognito on `/chat`, limits messages to 500 characters, caps responses at 220 tokens, and throttles this route to one request per second.

## Comparable EC2 baselines

AWS Price List API rates retrieved on 2026-09-24 for Singapore were: `t3.small` Linux $0.0264/hour, gp3 $0.096/GB-month, Application Load Balancer $0.0252/hour plus $0.008/LCU-hour, public IPv4 $0.005/hour, and NAT Gateway $0.059/hour plus data processing.

| Design | Monthly fixed hosting | Calculation |
|---|---:|---|
| Minimal, not highly available | **$24.84** | One `t3.small` ($19.27), 20 GB gp3 ($1.92), one public IPv4 ($3.65) |
| Two-instance web tier | **$73.92** | Two `t3.small` ($38.54), 40 GB gp3 ($3.84), ALB hours ($18.40), one average LCU ($5.84), two ALB IPv4 addresses ($7.30) |
| Private two-instance web tier | **$116.99** | Two-instance total plus one NAT Gateway hour charge ($43.07), before NAT data processing |

These EC2 figures intentionally keep Cognito, Bedrock, DynamoDB and analytical services unchanged so the comparison isolates web and API hosting. They exclude backup storage, additional NAT gateways, database replacement, traffic, monitoring growth and engineering time for patching, scaling and failover. A production multi-AZ design with one NAT Gateway per availability zone would be higher.

## Interpretation

For this low-volume, uneven university workload, serverless avoids roughly $21 to $113 of idle monthly infrastructure compared with the three EC2 baselines. EC2 can become competitive for consistently high utilization or specialized long-running workloads, but the measured workload does not justify always-on instances. Actual spend must be checked in AWS Cost Explorer after deployment.

## Pricing sources

- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)
- [Amazon EC2 On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/)
- [AWS Price List API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html)
