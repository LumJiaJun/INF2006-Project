# evidence/

Named, dated evidence artefacts cited by `project_manifest.yaml`.

| File | Purpose |
|------|---------|
| architecture-current.png | Final architecture export: global edge, identity, two-AZ private subnets with security groups, endpoints, data and analytics services, observability, Terraform, and the GitHub Actions CI/CD lane |
| architecture-full.drawio | Editable draw.io source for architecture-current.png |
| architecture-full-preview.png | Earlier script-generated preview of the same layout, superseded by architecture-current.png |
| architecture-cicd-terraform.drawio | Earlier standalone Terraform and CI/CD lane, now included in architecture-full.drawio |
| architecture-detailed.png | Detailed enterprise view of trust boundaries, routes, private networking, managed services, data engineering, monitoring, and delivery flows |
| architecture-detailed.svg | Editable source for the detailed enterprise architecture diagram |
| architecture.svg | Earlier SVG source for the previous numbered architecture diagram, superseded by architecture-full.drawio |
| architecture-security-audit-2026-09-28.md | Architecture and security audit findings |
| availability-review-2026-10-06.md | In-Region high-availability mechanisms, DynamoDB replication clarification, and regional recovery limitation |
| cloud-verification-2026-10-04.md | Redacted zero-drift, deployed workflow, Lambda, monitoring, recovery, Glue, S3, WAF, and SNS verification |
| verification-2026-09-30.txt | Redacted terminal transcript for current validation, live smoke checks, Terraform state, alarms, GitHub Actions, and DAST summary |
| verification-2026-10-01.txt | Redacted deployment and validation transcript for the contributor navigation integration |
| encryption-review-2026-10-01.md | Live encryption, public-access, recovery, and sensitive-logging verification |
| video-demonstration-guide.md | Redacted 5-8 minute functional and AWS service demonstration checklist |
| consultation-improvements-2026-10-01.md | Potential-host workflow, AI hardening, browser journey, deployment, and consultation validation |
| repository-audit-2026-10-01.md | Full repository, security, infrastructure, live-state, documentation, and evidence audit |
| repository-audit-2026-10-02.md | Final tracked-repository, local runtime, security-gate, branch, and submission-risk audit |
| deployment-security-retest-2026-10-03.md | Full redeployment, functional/security/load retest, discovered fixes, and verified teardown |
| application-live-review-2026-10-03.md | Local-first redeployment, real-data pipeline, application improvements, DynamoDB-backed chat proof, and final live controls |
| chatbot-accuracy-2026-10-04.md | Grounded prompt design, expanded local and deployed 24-scenario evaluation, DynamoDB isolation, Cognito enforcement, and residual AI limits |
| chatbot-evaluation-local-2026-10-06.json | Raw synthetic local Bedrock results for the 24 chatbot scenarios of 6 October |
| chatbot-evaluation-deployed-2026-10-06.json | Raw deployed Lambda results for the 24 scenarios of 6 October, user-partition isolation, and anonymous API rejection |
| chatbot-evaluation-deployed-2026-10-07.json | Raw deployed Lambda results for the 26-scenario suite after the market-grounding change |
| live-fixes-and-recheck-2026-10-07.md | Signed-in estimator CORS fix, grounded chatbot change, 26-scenario evaluation, live smoke, load, and security probes |
| manual-browser-verification-2026-10-07.md | Signed-in estimate, saved history, and chat recall observed in a browser after the CORS fix, with the checks still not verified |
| clean-zip-qa-2026-10-07.md | Clean-ZIP preflight run by Nixon, plus the manual journey and sign-off Ignatius must complete |
| owasp-top-10-2025-review.md | Current OWASP Top 10 awareness-category control and residual-risk mapping |
| teardown-2026-10-02.md | Reviewed application teardown, recovery procedure, verification, and remaining FinOps baseline |
| teardown-2026-10-04.md | Final reviewed destroy-only plan, interrupted-apply recovery, zero-state check, and AWS absence verification |
| rubric-gap-review-2026-10-02.md | Rubric criterion mapping, local preflight result, and remaining submission risks |
| iam-rbac-review-2026-10-02.md | User authorization, workload IAM, network scope, and regression-test review |
| local-development-2026-10-02.md | Loopback frontend, analytics, schema, and model-backed prediction verification |
| test-functional.md | Functional workflow test |
| test-security.md | Security control test |
| test-data-ai.md | Data / AI validation test |
| data-pipeline.md | Measured Glue, Parquet, and Athena pipeline evidence |
| test-resilience.md | Scalability / resilience / recovery test |
| test-load-safety-2026-09-28.md | Safe load-test guardrails and authorization controls |
| load-test-2026-10-04.txt | Redacted raw bounded-load output, matching CloudWatch metrics, and alarm states |
| test-web-load.md | Browser/static web-load test |
| prediction-runtime.md | Model container and Lambda runtime evidence |
| monitoring.md | Logging / monitoring evidence |
| cost-estimate.md | Cost assumptions and FinOps review |
| aws-pricing-calculator-2026-10-06.md | Saved AWS Pricing Calculator workload estimate, assumptions, interpretation, and verification status |
| aws-pricing-calculator-estimate-2026-10-06.csv | Redacted line-item export from the AWS Pricing Calculator workload estimate |
| cloud-verification-2026-10-06.md | Live zero-drift, functional, data-pipeline, security-control, image-scan, and chat verification |
| threat-control-map.md | Threat-to-control mapping + secrets handling |
| serverless-zero-trust-review.md | Serverless Lens and Zero Trust design review |
| ci-cd.md | GitHub Actions CI/CD, CodeQL SAST, OWASP ZAP DAST, and encrypted shared-state validation |
| github-security-runs-2026-10-06.md | Public GitHub CI, CodeQL, security-gate, and successful hosted ZAP DAST run verification |
| ../.github/workflows/security.yml | Pinned dependency and Python static-security gates |
| aws-serverless-reference-review-2026-09-28.md | Official AWS pattern comparison and VPC decision |
| vpc-deployment-2026-09-29.md | Two-AZ private Lambda VPC deployment and verification |
| edge-security-2026-09-29.md | CloudFront WAF, scoped CloudTrail, and ACM status |
| cross-region-recovery-plan.md | Regional recovery status, trade-offs, and implementation order |
| README.md | Evidence catalogue and redaction guidance |

Redact account IDs, public IPs, tokens and sensitive config. Prefer text/config
exports over screenshots. Do not include credentials or personal data.
