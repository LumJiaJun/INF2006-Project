# CI/CD and shared-state evidence

**Validation date:** 2026-09-28

**Validated commit:** `af9c604`

## GitHub Actions results

- CI completed successfully: https://github.com/LumJiaJun/INF2006-Project/actions/runs/36377882219
- CodeQL SAST completed successfully for Python and JavaScript/TypeScript: https://github.com/LumJiaJun/INF2006-Project/actions/runs/36377882314
- The CI run executed 25 unit tests, Python compilation, frontend JavaScript syntax checks, AWS identifier checks, Terraform formatting, and validation of both Terraform roots.
- Actions are pinned to full commit hashes. Workflow permissions are read-only by default; only the manual deployment workflow can request an OIDC token.

## Dynamic application security testing

`.github/workflows/dast.yml` defines a passive OWASP ZAP baseline scan using a
container pinned by digest. It runs after a successful development deployment
or by manual dispatch, accepts only an HTTPS URL whose hostname exactly matches
`DAST_ALLOWED_HOST`, uploads reports even when findings occur, and then fails
closed on ZAP warning, failure, or scan-error exit codes.

DAST has not been executed because the evidence deployment is currently
offline. `DAST_TARGET_URL` and `DAST_ALLOWED_HOST` must be configured in the
protected GitHub `development` environment after recreation. This records the
control without fabricating a scan result.

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

The application state contains no resources because the evidence deployment was
intentionally destroyed. A later recreation will start from the reviewed empty
application state rather than an untracked live stack.

## Deployment gate

The `Deploy development` workflow is intentionally manual and was not executed
during this validation. Before it can run, a maintainer must configure the
GitHub `development` environment, its approval policy, an AWS OIDC deployment
role, state bucket and KMS variables, and the private S3 URI of the evaluated
model artifact. This is an explicit incomplete operational prerequisite, not a
claim of automated deployment success.
