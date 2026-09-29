# evidence/

Named, dated evidence artefacts cited by `project_manifest.yaml`.

| File | Purpose |
|------|---------|
| architecture-current.png | Current labelled architecture, trust boundaries, data flows, and improvement roadmap |
| architecture.png | Earlier labelled architecture diagram retained for history |
| architecture.svg | Earlier editable architecture diagram retained for history |
| architecture-security-audit-2026-09-28.md | Architecture and security audit findings |
| test-functional.md | Functional workflow test |
| test-security.md | Security control test |
| test-data-ai.md | Data / AI validation test |
| data-pipeline.md | Measured Glue, Parquet, and Athena pipeline evidence |
| test-resilience.md | Scalability / resilience / recovery test |
| test-load-safety-2026-09-28.md | Safe load-test guardrails and authorization controls |
| test-web-load.md | Browser/static web-load test |
| frontend-and-lambda-load-2026-09-28.md | Frontend and Lambda load observations |
| live-deployment-test-2026-09-28.md | Historical deployment verification and limitations |
| prediction-runtime.md | Model container and Lambda runtime evidence |
| monitoring.md | Logging / monitoring evidence |
| cost-estimate.md | Cost assumptions and FinOps review |
| threat-control-map.md | Threat-to-control mapping + secrets handling |
| serverless-zero-trust-review.md | Serverless Lens and Zero Trust design review |
| adheesh-branch-review.md | Compatibility review of Adheesh's parallel implementation |
| ci-cd.md | GitHub Actions and encrypted shared-state validation |
| ../.github/workflows/security.yml | Pinned dependency and Python static-security gates |
| aws-serverless-reference-review-2026-09-28.md | Official AWS pattern comparison and VPC decision |
| vpc-deployment-2026-09-29.md | Two-AZ private Lambda VPC deployment and verification |
| edge-security-2026-09-29.md | CloudFront WAF, scoped CloudTrail, and ACM status |
| cross-region-recovery-plan.md | Regional recovery status, trade-offs, and implementation order |
| README.md | Evidence catalogue and redaction guidance |

Redact account IDs, public IPs, tokens and sensitive config. Prefer text/config
exports over screenshots. Do not include credentials or personal data.
