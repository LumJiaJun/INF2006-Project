# evidence/

Named, dated evidence artefacts cited by `project_manifest.yaml`.

| File | Purpose |
|------|---------|
| architecture-current.png | Current numbered architecture showing WAF, CloudFront, Cognito, two-AZ Lambda VPC, endpoints, data stores, operations, and CI/CD |
| architecture-detailed.png | Detailed enterprise view of trust boundaries, routes, private networking, managed services, data engineering, monitoring, and delivery flows |
| architecture-detailed.svg | Editable source for the detailed enterprise architecture diagram |
| architecture.svg | Editable source for the current numbered architecture diagram |
| architecture-security-audit-2026-09-28.md | Architecture and security audit findings |
| verification-2026-09-30.txt | Redacted terminal transcript for current validation, live smoke checks, Terraform state, alarms, GitHub Actions, and DAST summary |
| verification-2026-10-01.txt | Redacted deployment and validation transcript for the contributor navigation integration |
| encryption-review-2026-10-01.md | Live encryption, public-access, recovery, and sensitive-logging verification |
| video-demonstration-guide.md | Redacted 5-8 minute functional and AWS service demonstration checklist |
| consultation-improvements-2026-10-01.md | Potential-host workflow, AI hardening, browser journey, deployment, and consultation validation |
| repository-audit-2026-10-01.md | Full repository, security, infrastructure, live-state, documentation, and evidence audit |
| teardown-2026-10-02.md | Reviewed application teardown, recovery procedure, verification, and remaining FinOps baseline |
| rubric-gap-review-2026-10-02.md | Rubric criterion mapping, local preflight result, and remaining submission risks |
| iam-rbac-review-2026-10-02.md | User authorization, workload IAM, network scope, and regression-test review |
| local-development-2026-10-02.md | Loopback frontend, analytics, schema, and model-backed prediction verification |
| test-functional.md | Functional workflow test |
| test-security.md | Security control test |
| test-data-ai.md | Data / AI validation test |
| data-pipeline.md | Measured Glue, Parquet, and Athena pipeline evidence |
| test-resilience.md | Scalability / resilience / recovery test |
| test-load-safety-2026-09-28.md | Safe load-test guardrails and authorization controls |
| test-web-load.md | Browser/static web-load test |
| prediction-runtime.md | Model container and Lambda runtime evidence |
| monitoring.md | Logging / monitoring evidence |
| cost-estimate.md | Cost assumptions and FinOps review |
| threat-control-map.md | Threat-to-control mapping + secrets handling |
| serverless-zero-trust-review.md | Serverless Lens and Zero Trust design review |
| ci-cd.md | GitHub Actions and encrypted shared-state validation |
| ../.github/workflows/security.yml | Pinned dependency and Python static-security gates |
| aws-serverless-reference-review-2026-09-28.md | Official AWS pattern comparison and VPC decision |
| vpc-deployment-2026-09-29.md | Two-AZ private Lambda VPC deployment and verification |
| edge-security-2026-09-29.md | CloudFront WAF, scoped CloudTrail, and ACM status |
| cross-region-recovery-plan.md | Regional recovery status, trade-offs, and implementation order |
| README.md | Evidence catalogue and redaction guidance |

Redact account IDs, public IPs, tokens and sensitive config. Prefer text/config
exports over screenshots. Do not include credentials or personal data.
