# Cross-Region Recovery Plan

## Current state

The application is deployed in `ap-southeast-1`. DynamoDB prediction history
has point-in-time recovery enabled in that region. The new idempotency table is
short-lived coordination state with TTL and does not need cross-region
replication. S3 data is versioned and encrypted, but cross-region replication
is not currently provisioned. There is no tested cross-region failover.

## Why this is not enabled automatically

Cross-region recovery is an architectural and cost decision, not a harmless
Terraform toggle. It requires a selected DR region, an agreed recovery point
objective (RPO), recovery time objective (RTO), data-residency acceptance,
cross-region IAM/KMS design, replicated frontend/data artefacts, and a tested
DNS or endpoint cutover. Creating a second region without those decisions can
produce an untested and costly partial failover path.

## Recommended implementation order

1. Select a DR region and document RPO/RTO and monthly budget.
2. Use an AWS-managed backup/copy design for the prediction-history table, or
   DynamoDB global-table replication if near-real-time recovery is required.
3. Replicate only the required S3 data-lake prefixes with destination-region
   encryption and a scoped replication role.
4. Recreate the API, Cognito configuration, Lambda image, and observability
   resources from Terraform in the DR region.
5. Add an explicit failover procedure and test restore plus application cutover
   without exposing credentials or personal data in evidence.

Until those choices are approved, the current honest control is regional PITR
plus Terraform recreation, not a claimed multi-region disaster-recovery
service.
