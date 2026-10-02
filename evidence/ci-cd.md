# CI/CD and shared-state evidence

**Validation date:** 2026-09-30

**Baseline CI validated commit:** `2e67d0f`

**DAST remediation commit:** `395c79b`

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
closed on scan errors, new warnings, and rules marked `FAIL`. Reviewed static
site exceptions are narrow, justified, and version controlled in
`.zap/rules.tsv`.

GitHub DAST run `36689377727` was manually dispatched against the allowlisted
CloudFront deployment on 2026-09-30 at commit `937cfd4`. Target validation,
reachability, the passive scan, and report upload succeeded. The final gate
failed because ZAP returned warning exit code 2. The uploaded artifact
`zap-baseline-36689377727` is retained by GitHub until 2026-10-30.

An exact local reproduction with the pinned container crawled 175 URLs and
reported zero failed alerts and six warning categories: cache-control review,
suspicious source comments, a potential-XSS heuristic, the generic AmazonS3
server header, static-content cacheability, and a missing
`Cross-Origin-Embedder-Policy` header. The source comments were removed, the
CloudFront response policy now adds `Cross-Origin-Embedder-Policy:
require-corp`, and the remaining platform or static-site heuristics have narrow
reviewed dispositions in `.zap/rules.tsv`.

Terraform applied the remediation with 0 resources added, 4 changed in place,
and 0 destroyed. After CloudFront deployment and invalidation, the same pinned
scan with the repository policy crawled 175 URLs and returned exit code 0 with
0 failed rules, 0 warnings, 63 passed rules, and 4 reviewed ignored rules. The
GitHub workflow must still be rerun from the corrected commit; a passing GitHub
run is not yet claimed.

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

The application stack was redeployed and retested in the configured Singapore
development account on 2-3 October 2026, then destroyed after evidence
collection. Terraform state and direct service inventories reported zero
remaining application resources. The functional, security, bounded-load, image
scan, and local DAST results are recorded in
`evidence/deployment-security-retest-2026-10-03.md`. State remains outside Git.

## Deployment gate

The `Deploy development` workflow is intentionally manual and was not invoked
during this evidence run; the live stack was applied from the reviewed local
Terraform configuration. Before the GitHub workflow can run, a maintainer must configure the
GitHub `development` environment, its approval policy, an AWS OIDC deployment
role, state bucket and KMS variables, and the private S3 URI of the evaluated
model artifact. This is an explicit incomplete operational prerequisite, not a
claim of automated deployment success.
