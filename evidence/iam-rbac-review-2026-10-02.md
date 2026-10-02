# IAM and Authorization Scope Review - 2026-10-02

## Authorization model

The application does not invent an administrator role because no implemented
administrator workflow requires one. Its user authorization boundary is:

- anonymous visitors may call health, analytics, and unsaved prediction routes;
- authenticated Cognito users may save predictions, read history, and use the
  cost-bearing chat route;
- API Gateway validates JWT issuer and audience before protected invocation;
- Lambda derives ownership from the verified `sub` claim rather than a supplied
  user identifier;
- DynamoDB queries use that subject as the partition key.

This is route-based authorization plus user-attribute isolation, not a claim of
complex enterprise RBAC. Adding decorative Cognito groups would increase
configuration without protecting an actual role-specific workflow.

## Workload IAM

Each Lambda has a distinct execution role. Prediction can write history and
idempotency records, history can query only the history table, analytics can run
the fixed Athena workload and access the required catalog/S3 paths, chat can
invoke the selected Bedrock model and query history, and health can only write
its logs. API Gateway invoke permissions are scoped by method and route ARN.

The EC2 network-interface actions used by VPC-attached Lambda functions retain
`Resource = "*"` because those EC2 API actions do not support reliable
resource-level restriction for the Lambda execution path. This exception is
limited to create, describe, and delete network interfaces and is not an EC2
instance-management permission.

## Network scope improvement

The Lambda security group no longer allows HTTPS egress to `0.0.0.0/0`.
Interface endpoint traffic is limited to the application VPC CIDR, while S3 and
DynamoDB traffic is limited to the regional managed prefix lists exposed by the
gateway endpoints. No NAT Gateway or internet route exists.

## Regression checks

`tests/test_infrastructure_security.py` verifies that protected routes retain
JWT authorization, every Lambda retains a purpose-specific role, and Lambda
egress does not regress to an internet-wide CIDR.
