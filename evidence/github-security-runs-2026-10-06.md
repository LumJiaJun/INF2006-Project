# GitHub Security Workflow Verification - 2026-10-06

## Objective

Verify the current public GitHub Actions status and close the stale statement
that the remediated OWASP ZAP workflow had not recorded a successful hosted
run.

## Method

The public GitHub Actions API was queried for the repository workflow runs,
the successful DAST run, its job steps, and its retained artefact. No GitHub
token, repository secret, cloud identifier, target hostname, or scan output was
stored in this evidence.

## Current branch gates

The following public runs completed successfully for commit `58d3dad` on
`main` after the final architecture update:

| Workflow | Run | Result |
|----------|-----|--------|
| CI | [37419611142](https://github.com/LumJiaJun/INF2006-Project/actions/runs/37419611142) | Success |
| SAST - CodeQL | [37419611206](https://github.com/LumJiaJun/INF2006-Project/actions/runs/37419611206) | Success |
| Security gates | [37419611086](https://github.com/LumJiaJun/INF2006-Project/actions/runs/37419611086) | Success |

## Hosted DAST result

GitHub DAST run
[36699009812](https://github.com/LumJiaJun/INF2006-Project/actions/runs/36699009812)
was manually dispatched from `main` at commit `d8c9798` on 2026-09-30. The
workflow and its `DAST baseline scan` job completed successfully. GitHub
reported successful target validation, reachability, passive ZAP execution,
and report upload. The fail-closed enforcement step was skipped because the
scan step succeeded.

The retained public run metadata listed artefact
`zap-baseline-36699009812`, created on 2026-09-30 with a 30-day retention
period. The artefact may expire after that retention window, so the workflow
file, run URL, dated result, and local pinned reproduction remain the durable
evidence trail.

## Interpretation

The earlier failed hosted run remains useful proof that the pipeline fails
closed on ZAP warnings. The later successful hosted run proves that the
remediated policy and site passed the same GitHub workflow. This is a passive
baseline result, not an authenticated penetration test or proof that every
future deployment is vulnerability-free.
