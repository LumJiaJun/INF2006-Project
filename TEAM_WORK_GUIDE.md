# Team Work Guide

Class: EP2, Group: G014

This guide explains how to work on the current Airbnb Pricing and Market
Intelligence Platform consistently, safely, and with clear team coordination.

## Repository and branches

- `main` is the shared submission branch.
- `nixon` contains the current cloud/infrastructure implementation and is
  already merged into `main`.
- `origin/adheesh` is preserved separately because it contains the StaySphere
  FastAPI application, synthetic demo data, and a different API contract. Ideas
  from it can be adapted after checking that they fit this serverless design.
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
5. Coordinate before running `apply` or `destroy` if another teammate is
   working on the shared stack. State lockfiles help prevent concurrent
   Terraform operations, but they do not replace team coordination.
6. Keep the team updated whenever you plan, apply, or destroy AWS resources.
   Share the planned change, result, and any important outputs in the team
   chat so everyone can avoid conflicts and reproduce the work.

## AWS access setup

Use temporary credentials whenever possible. The project owner should grant
each teammate only the permissions needed for their assigned work.

### Preferred: IAM Identity Center

1. Ask the project owner for the AWS access portal URL and the assigned account
   and permission set.
2. Sign in through the access portal using the invitation or school identity.
3. Install or update the AWS CLI, then run `aws configure sso`.
4. Choose the assigned account, role, region `ap-southeast-1`, and a profile
   name such as `inf2006-dev`.
5. Sign in when prompted and verify the session:

   ```powershell
   aws sso login --profile inf2006-dev
   aws sts get-caller-identity --profile inf2006-dev
   ```

6. Use the profile for Terraform commands:

   ```powershell
   $env:AWS_PROFILE = "inf2006-dev"
   ```

### Fallback: individual access key

Use this only when IAM Identity Center is unavailable and the project owner
has approved it. Never use the root account or share keys with teammates.

1. In the AWS Console, open IAM, select the assigned user, and open
   **Security credentials**.
2. Select **Create access key**, choose **Command Line Interface (CLI)**, and
   complete the confirmation step.
3. Copy the secret access key immediately into a secure password manager. AWS
   shows it only once; do not paste it into GitHub, chat, Terraform variables,
   `backend.hcl`, or screenshots.
4. Configure the local AWS CLI without placing the values in the repository:

   ```powershell
   aws configure --profile inf2006-dev
   aws sts get-caller-identity --profile inf2006-dev
   ```

5. Set the profile for the current PowerShell session before Terraform:

   ```powershell
   $env:AWS_PROFILE = "inf2006-dev"
   ```

6. Delete or rotate the key when the work is complete. If a key is exposed,
   disable it immediately in IAM and notify the project owner.

Do not put access keys in Terraform files, GitHub secrets for local work,
`.env` files, commit messages, or evidence. GitHub Actions uses OIDC rather
than long-lived AWS access keys.

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

Post the planned change and final result in the team chat after every apply,
including frontend-only updates, so the team has a shared record.

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

Avoid `terraform destroy -auto-approve` on the shared environment. Coordinate
with the team first, post the destroy plan in the team chat, save required
evidence, and verify the destroy result.

## Current workstreams

Suggested contribution areas include:

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
`TEAM_CONTRIBUTIONS.md` so the contribution record stays accurate.

## Current known constraints

- The development account Lambda concurrency quota is now 1,000 in
  `ap-southeast-1`. API Gateway route throttling still rejects excess traffic;
  the approved-quota stress result is recorded in `evidence/test-resilience.md`.
- No cross-region replica or tested regional failover is deployed.
- The SNS operational alert email is confirmed for the current environment;
  a replacement endpoint must be confirmed again if the Terraform variable
  changes.
- ECR scan-on-push is enabled. The latest recorded image scan completed with
  no findings; future image builds still need their scan result checked.
- The model estimates listing price from a cross-sectional dataset; it does
  not prove future prices, demand, or condition monitoring.

Read `README.md`, `src/infrastructure/README.md`, and the dated files under
`evidence/` before changing architecture or updating claims.
