# Official AWS Serverless Reference Review - 2026-09-28

## Scope

This review compares the current platform with official AWS serverless samples,
the AWS Serverless Applications Lens, and the AWS serverless multi-tier
reference architecture. It is a design cross-check, not a claim that the
project is production certified.

## References reviewed

- AWS sample: [amazon-cognito-api-gateway](https://github.com/aws-samples/amazon-cognito-api-gateway)
- AWS sample: [sam-python-crud-sample](https://github.com/aws-samples/sam-python-crud-sample)
- AWS sample: [lambda-refarch-webapp](https://github.com/aws-samples/lambda-refarch-webapp)
- [AWS Serverless Applications Lens](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/)
- [AWS Serverless Multi-Tier Architectures with API Gateway and Lambda](https://docs.aws.amazon.com/whitepapers/latest/serverless-multi-tier-architectures-api-gateway-lambda/)

## Pattern comparison

| AWS reference pattern | Current implementation | Decision |
|---|---|---|
| Cognito user pool tokens protect API Gateway routes | Cognito authorization-code flow with PKCE, required TOTP MFA, and API Gateway JWT routes protect history, saved predictions, and chat | Retained |
| API Gateway fronts focused Lambda handlers | HTTP API routes invoke separate health, prediction, history, analytics, and chat functions | Retained |
| DynamoDB follows the application's access pattern | History uses `user_id` plus a time-ordered sort key and queries only the verified JWT subject | Retained |
| Each function has a purpose-specific IAM role | Terraform scopes prediction, history, analytics, Glue, and chat roles separately | Retained |
| Static web assets use CloudFront and S3 | CloudFront serves the private S3 origin through Origin Access Control | Retained |
| VPC/private subnets are used when a function must reach private-subnet resources | No current function needs RDS, ElastiCache, or another private-subnet dependency | Not added |

## VPC boundary

There is no VPC, subnet, NAT Gateway, security group, or VPC endpoint in the
current Terraform root. DynamoDB is an AWS-managed regional service and is not
placed inside a customer VPC. This is consistent with the reviewed serverless
patterns for a Lambda/API Gateway/DynamoDB application.

Adding a minimal VPC would not make the current DynamoDB table private. It
would require moving selected Lambdas into subnets and then designing routes,
security groups, service endpoints, and outbound access. A NAT Gateway would
also add recurring cost. The current identity, IAM, API throttling, S3 OAC,
encryption, validation, and logging controls provide the relevant V1 boundary.

If a future requirement introduces RDS, ElastiCache, a private third-party
connection, or another subnet-only dependency, revisit the design in this
order: private subnets, least-privilege security groups, gateway endpoints for
S3 and DynamoDB where applicable, and only then a justified egress path.

## Refinements confirmed

- Keep JWT authorization at API Gateway and derive history ownership from the
  verified `sub` claim in backend code.
- Keep separate IAM roles and avoid broad service permissions.
- Keep fixed Athena queries rather than accepting user SQL.
- Keep bounded chat input/output, protected chat access, and user-scoped
  DynamoDB context; do not promote the optional assistant to the V1 core.
- Keep the current no-custom-domain ACM decision. CloudFront's generated domain
  already provides managed HTTPS; ACM becomes relevant after an owned domain
  and DNS validation exist.

## Remaining evidence work

- Regenerate `report.pdf` from the corrected report source before submission.
- Replace the stale report test count and ECR scan wording with current evidence.
- Complete `TEAM_CONTRIBUTIONS.md` with genuine team-provided roles, artefacts,
  test ownership, and reflections.
