# Private Lambda VPC deployment evidence - 2026-09-29

## Design

- Terraform created one project VPC with CIDR `10.20.0.0/16`.
- Two private subnets were created across the first two available Singapore availability zones: `10.20.1.0/24` and `10.20.2.0/24`.
- Each subnet has its own route table and no public IP assignment.
- A Lambda security group permits outbound HTTPS only. An endpoint security group permits inbound HTTPS only from the Lambda security group.
- No internet gateway and no NAT Gateway were created.

## Private service access

- S3 and DynamoDB use gateway endpoints attached to both private route tables.
- CloudWatch Logs, Athena, and Bedrock Runtime use interface endpoints in both private subnets with private DNS enabled.
- DynamoDB remains an AWS-managed regional service. The endpoint provides private VPC routing to DynamoDB; it does not place the table inside the VPC.

## Lambda attachment

The health, prediction, analytics, history, and chat Lambdas all use the two private subnet IDs and the dedicated Lambda security group. Each execution role received only the EC2 network-interface actions required for Lambda VPC attachment: create, describe, and delete network interfaces.

## Deployment and tests

- Terraform validation passed before deployment.
- The VPC and endpoint plan contained 19 additions and zero destroys.
- The subsequent Lambda attachment plan contained five in-place updates and zero destroys.
- All five VPC endpoints reported `available`.
- The live smoke suite passed health, prediction, ten-city analytics, protected-route HTTP 401 checks, security headers, and malformed-input validation after attachment.
- Direct authorized test events returned HTTP 200 from the history Lambda with an empty test-subject result and from the chat Lambda with a bounded Claude Haiku response, confirming DynamoDB and Bedrock access through the private endpoints.
- Terraform reported `No changes` after deployment.
- The local Python suite remained green with 29 passing tests.

## Trade-offs and remaining checks

This design improves network-path control and provides two-AZ Lambda ENI placement, but it does not replace Cognito, IAM, input validation, encryption, or monitoring. Interface endpoints create hourly and data-processing charges, and VPC-attached Lambdas can have higher cold-start and deployment complexity. A NAT Gateway was intentionally avoided because the current functions only require the AWS services covered by the endpoints. Cross-region recovery remains a separate, unimplemented requirement.
