# CI/CD and shared-state evidence

**Validation date:** 2026-09-28

**Validated commit:** `2e67d0f`

## GitHub Actions results

- CI completed successfully: https://github.com/LumJiaJun/INF2006-Project/actions/runs/36418939012
- CodeQL SAST completed successfully for Python and JavaScript/TypeScript: https://github.com/LumJiaJun/INF2006-Project/actions/runs/36418939014
- CI executed 26 unit tests, Python compilation, frontend JavaScript syntax checks, AWS identifier checks, Terraform formatting, and validation of both Terraform roots.
- `.github/workflows/security.yml` adds separate pinned `pip-audit` checks for application and analytics dependencies plus Bandit scanning for Python source. The new security workflow requires a successful run before it should be configured as a protected branch check.
- Actions are pinned to full commit hashes. Workflow permissions are read-only by default; only the manual deployment workflow can request an OIDC token.

## Dynamic application security testing

`.github/workflows/dast.yml` defines a passive OWASP ZAP baseline scan using a
container pinned by digest. It runs after a successful development deployment
or by manual dispatch, accepts only an HTTPS URL whose hostname exactly matches
`DAST_ALLOWED_HOST`, uploads reports even when findings occur, and then fails
closed on ZAP warning, failure, or scan-error exit codes.

The pinned local ZAP baseline scan was executed against the live CloudFront
deployment on 2026-09-28. It found no high-risk alerts; five warning categories
remain under review, including intentional static caching and a crawler
heuristic that needs a frontend regression test. The GitHub DAST workflow is
configured but has not been invoked because its protected environment variables
are not yet configured. No GitHub DAST result is claimed.

The first CI run exposed that `boto3` was available on the deployment computer
but missing from a clean runner. `tests/requirements.txt` now declares it
explicitly, and the test suite also passed in a newly created local virtual
environment before the corrected workflow was pushed.

## Shared state result

The state bootstrap was applied once to adopt the existing empty state bucket.
The final bootstrap plan reported no changes. Verification confirmed S3
versioning, `aws:kms` default encryption, an S3 bucket key, public-access
blocking, TLS-only access, and native S3 lockfile configuration. Account IDs,
key ARNs, backend configuration, Terraform state, and plan files remain outside
Git.

The application stack is currently live in the configured Singapore development
account. Terraform returned `No changes` after deployment, and the live
functional, security, bounded-load, and local DAST results are recorded in
`evidence/live-deployment-test-2026-09-28.md`. State remains outside Git.

## Deployment gate

The `Deploy development` workflow is intentionally manual and was not invoked
during this evidence run; the live stack was applied from the reviewed local
Terraform configuration. Before the GitHub workflow can run, a maintainer must configure the
GitHub `development` environment, its approval policy, an AWS OIDC deployment
role, state bucket and KMS variables, and the private S3 URI of the evaluated
model artifact. This is an explicit incomplete operational prerequisite, not a
claim of automated deployment success.
