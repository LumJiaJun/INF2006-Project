# Availability and Recovery Review - 2026-10-06

## Objective

Determine whether the Terraform-defined architecture tolerates an Availability
Zone impairment, clarify what one DynamoDB service represents, and state the
remaining recovery boundary without claiming multi-Region availability.

## Configuration reviewed

- `src/infrastructure/network.tf`
- `src/infrastructure/data.tf`
- Lambda `vpc_config` blocks in the Terraform root
- `evidence/cloud-verification-2026-10-04.md`
- `evidence/cross-region-recovery-plan.md`

## Findings

| Layer | Implemented availability mechanism | Boundary |
|------|------------------------------------|----------|
| Edge | CloudFront and its associated WAF protect the public frontend path at the AWS edge | The S3 origin and API remain in one AWS Region |
| API and identity | API Gateway and Cognito are regional managed services with no customer-operated instance | No secondary regional application endpoint is deployed |
| Compute | All five Lambda functions are configured with private subnets in two Availability Zones | Lambda placement is service-managed; the project does not pin duplicate functions to individual AZs |
| Private connectivity | Logs, Athena, and Bedrock Runtime interface endpoints have endpoint interfaces in both private subnets; S3 and DynamoDB gateway endpoints are attached to both private route tables | No NAT Gateway or general internet route is present |
| Application records | DynamoDB contains two logical tables: prediction history and idempotency. DynamoDB automatically replicates table data across three Availability Zones in the Region | Global tables and a second regional API stack are not deployed |
| Recovery | Prediction history has point-in-time recovery; S3 is versioned; Terraform and immutable ECR images support recreation | PITR protects against accidental data changes but is not automatic regional failover |

## Interpretation

The architecture is designed for high availability within `ap-southeast-1`:
an individual subnet or Availability Zone impairment should not remove every
configured Lambda network path, and DynamoDB does not depend on one customer-
managed database server. A single DynamoDB service box in the architecture
diagram therefore does not represent a single machine or single-AZ database.

The application is not multi-Region highly available. A complete Singapore
Region outage requires recreation or a future secondary deployment. DynamoDB
global tables alone would not solve this because the API, compute, identity,
frontend origin, analytics, monitoring, and traffic-routing layers would also
need a tested regional design.

## Official references

- [DynamoDB resilience and disaster recovery](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/disaster-recovery-resiliency.html)
- [AWS Security Hub Lambda multi-AZ control](https://docs.aws.amazon.com/securityhub/latest/userguide/lambda-controls.html#lambda-5)
- [AWS Well-Architected Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html)

## Conclusion

Use the claim `in-Region multi-AZ availability with a documented single-Region
recovery limitation`. Do not claim cross-Region failover, zero downtime, or a
tested regional disaster recovery deployment.
