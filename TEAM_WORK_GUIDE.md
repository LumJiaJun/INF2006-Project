# Team Work Guide

Class: EP2  
Group: G014

This guide explains how to work on the current Airbnb Pricing and Market
Intelligence Platform without overwriting another person's deployment or
claiming work that was not performed.

## Repository and branches

- `main` is the shared submission branch.
- `nixon` contains the current cloud/infrastructure implementation and is
  already merged into `main`.
- `origin/adheesh` is preserved separately because it contains the StaySphere
  FastAPI application, synthetic demo data, and a different API contract. Do
  not copy its runtime files into this serverless application without an
  explicit design review.
- Create a feature branch from the latest `main`, run focused checks, and open
  a pull request. Do not force-push shared branches.

## Before changing AWS

1. Confirm the AWS account and region: `ap-southeast-1`.
2. Confirm your AWS identity:

   ```powershell
   aws sts get-caller-identity
   aws configure get region
   ```

3. Work from `src/infrastructure` and use the shared encrypted backend. Do
   not use local state for the shared deployed stack.
4. Never commit credentials, `.env` files, `backend.hcl`, Terraform state,
   plan files, raw datasets, or model binaries.
5. Never run `apply` or `destroy` while another teammate is changing the
   shared stack. State lockfiles prevent concurrent Terraform operations, but
   they do not replace team coordination.

## First-time Terraform setup

The `bootstrap` Terraform root creates the private state bucket. A teammate
who has not configured the backend should obtain approved backend values from
the project owner, create an ignored `src/infrastructure/backend.hcl` from
`backend.hcl.example`, and initialize:

```powershell
cd src/infrastructure
terraform init -backend-config=backend.hcl
terraform state list
```

Do not paste backend values, account IDs, or state output into commits or
public evidence.

## Safe validation and apply workflow

Run these commands before requesting a deployment:

```powershell
cd src/infrastructure
terraform fmt -check
terraform validate
terraform plan -out=tfplan
terraform show -no-color tfplan
```

Review the plan for unexpected destroys, replacements, public access, IAM
policy expansion, or changes to Cognito and DynamoDB. If it is expected,
apply the reviewed plan:

```powershell
terraform apply tfplan
terraform output frontend_url
terraform output health_url
```

After changes, run focused checks from the repository root:

```powershell
cd ../..
python -m unittest discover -s tests -p "test_*.py" -q
node --check src/frontend/app.js
node --check src/frontend/auth.js
node --check src/frontend/chat.js
node --check src/frontend/markets.js
```

If frontend assets changed, invalidate CloudFront using the documented command
in `src/infrastructure/README.md`, then run the authorized smoke test.

## Destroy and cleanup

Destroy is only for an agreed cleanup window after evidence and screenshots
are complete. The development data-lake bucket is configured for intentional
cleanup, so required artefacts must be saved before destroying it.

```powershell
cd src/infrastructure
terraform plan -destroy -out=destroy.tfplan
terraform show -no-color destroy.tfplan
terraform apply destroy.tfplan
```

Never use `terraform destroy -auto-approve` on the shared environment. Confirm
with the team first, save required evidence, and verify the destroy plan.

## Current workstreams

Teammates can earn credit through genuine work in any of these areas:

- **Data and ML:** reproducible EDA, per-city error analysis, defensible model
  comparisons, currency documentation, and training-serving consistency.
- **Frontend and UX:** accessibility, responsive layouts, loading/error states,
  prediction explanations, analytics labels, history, and protected chat.
- **Testing and security:** multi-user isolation, authenticated idempotency
  retry testing, DAST review, and IAM/security evidence.
- **Analytics and data engineering:** approved Athena queries, Parquet
  validation, query cost/latency evidence, and descriptive analytics wording.
- **Operations and resilience:** alarm ownership, confirmed SNS endpoint,
  cross-region recovery design, and authorized load testing after quota review.
- **Documentation and submission:** genuine contribution records, refreshed
  evidence, rubric review, and PDF regeneration from the updated report.

Record each person's actual role, artefacts, tests, and reflection in
`TEAM_CONTRIBUTIONS.md`; do not copy a suggested workstream as proof of work.

## Current known constraints

- The development account has a Lambda concurrency quota of 10.
- No cross-region replica or tested regional failover is deployed.
- SNS has no confirmed human subscription by default.
- ECR scan-on-push is enabled, but the latest manual scan was limited by the
  per-image scan quota.
- The model estimates listing price from a cross-sectional dataset; it does
  not prove future prices, demand, or condition monitoring.

Read `README.md`, `src/infrastructure/README.md`, and the dated files under
`evidence/` before changing architecture or updating claims.
