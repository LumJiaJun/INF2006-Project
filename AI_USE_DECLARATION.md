# AI Use Declaration

Declare all AI tools and external baselines used, where they were used, the
verification the team performed, and any licences/attribution.

## Tools used

| Tool | Where it was used | Purpose |
|------|-------------------|---------|
| OpenAI Codex | `AGENTS.md`, `.gitignore`, `README.md`, `src/`, `tests/`, `evidence/`, and `project_manifest.yaml` | Repository inspection, implementation support, Terraform configuration, tests, documentation, and deployment verification. |
| Anthropic Claude Code (Claude Sonnet 5.5) | Final cleanup on 7 October 2026: `src/infrastructure/api.tf` (CORS), `src/backend/chat/`, `tests/evaluate_chatbot.py`, `tests/test_chat.py`, `README.md`, `report.md`, `evidence/`, and the draw.io architecture diagrams | Diagnosed and fixed the signed-in estimator CORS defect, grounded the chatbot in market statistics, ran verification and security probes, drafted evidence and documentation updates, and built the draw.io diagram. |
| OpenAI ChatGPT | Wording of `TEAM_CONTRIBUTIONS.md`, the clean-ZIP QA record, and related report and README sentences, edited by Nixon on 8 October 2026; and on 10 October 2026 the `.github/workflows/submission-zip.yml` workflow and the matching packaging paragraph in `README.md` | Softened and clarified wording of contribution and QA descriptions. It did not add completed work for any member; contribution entries remain subject to each member's own verification. |
| OpenAI image generation (gpt-image models, run through Codex) | `src/frontend/assets/global-markets.webp`, `src/frontend/assets/terrace-analytics.webp`, and `src/infrastructure/assets/cognito-background.jpg`, generated on 23 September 2026 | Decorative illustrations for the site and the Cognito sign-in page. They are AI-generated, are not photographs of real properties or people, and carry no data. The team did not record the prompts in the repository; the generation is evidenced by the operator's local Codex session records and by image dimensions that match the committed files. |
| Astra (used by Leow Yi Hao Ignatius) | Independent sanity review dated 9 October 2026 (clean Windows reproduction, report comparison, targeted probes) | Produced a prioritised list of defects and wording issues. Nixon validated each finding against the code before acting (`evidence/sanity-review-fixes-2026-10-09.md`). The tool's model and version were not recorded. |
| Amazon Bedrock Claude Haiku 4.5 | Deployed `POST /chat` application feature | Answers authenticated, project-scoped user questions through a bounded prompt and response interface. |

## Sources and baselines

| Source / baseline | URL | Licence | Modifications made by the team |
|-------------------|-----|---------|--------------------------------|
| Airbnb Listings & Reviews dataset | https://www.kaggle.com/datasets/mysarahmadbhat/airbnb-listings-reviews/data | CC0 1.0 Public Domain | Profiled data quality, selected features, created a reproducible model pipeline, built a Glue transform, and exposed constrained aggregate analytics. |
| AWS Architecture Icons | https://aws.amazon.com/architecture/icons/ | Used under AWS's published icon usage terms | SVG copies for offline diagram rendering are in `evidence/aws-icons/`; the final diagram was composed with the same icons in draw.io. |
| draw.io (diagrams.net) and its AWS shape library | https://www.diagrams.net/ | draw.io application is Apache-2.0; shapes depict AWS services per AWS's terms | Used to draw `evidence/architecture-full.drawio` and export `evidence/architecture-current.png`. |
| scikit-learn | https://scikit-learn.org/ | BSD-3-Clause | Used standard preprocessing and regression estimators; project-specific training, evaluation, validation, and deployment code is maintained in `analytics/` and `src/backend/predict/`. |

## Verification performed

| Area | Team verification | Evidence |
|------|-------------------|----------|
| Repository and Terraform | Ran 53 unit tests, the loopback frontend/API smoke journey, JavaScript syntax checks, `terraform fmt -check`, `terraform validate`, and a post-apply no-change plan. | `evidence/cloud-verification-2026-10-04.md`, `evidence/chatbot-accuracy-2026-10-04.md`, `evidence/local-development-2026-10-02.md` |
| Live application | Ran the deployed smoke script for frontend assets and headers, health, prediction, ten-city analytics, anonymous authorization rejection, malformed input, bounded what-if scenarios, and responsive visual review. | `evidence/application-live-review-2026-10-03.md`, `evidence/test-functional.md` |
| Data and model | Reproduced profiling, all full-data candidate metrics and the exported model hash, cross-checked submitted artefacts, and verified the Glue transformation, Parquet output, Athena scan size, and ten-city response. | `evidence/test-data-ai.md`, `evidence/data-pipeline.md` |
| Authentication and AI | Completed a consented Cognito journey, a Bedrock-plus-DynamoDB integration check, and local plus deployed chatbot evaluations (16 scenarios at first, 26 deployed scenarios on 7 October) without retaining credentials, codes, tokens, production records, or prompts. | `evidence/chatbot-accuracy-2026-10-04.md`, `evidence/application-live-review-2026-10-03.md`, `evidence/test-security.md` |
| Storage and IAM | Checked S3 public-access controls, direct-access denial, DynamoDB PITR, claim-derived history access, and selected allowed and denied IAM actions. | `evidence/test-security.md`, `evidence/threat-control-map.md` |
| Monitoring | Triggered and reset the prediction alarm, observed successful encrypted SNS publication, and received the operator email. | `evidence/monitoring.md` |
| Load and resilience | Retained both successful bounded tests and the earlier quota-related 503 result; the approved-quota retest produced only HTTP 200 and controlled HTTP 429 responses. | `evidence/test-web-load.md`, `evidence/test-resilience.md` |
| CI security | Checked successful CI, CodeQL, dependency audit, Bandit, image scan-on-push, two successful pinned local ZAP runs, WAF blocking, and the OWASP Top 10:2025 control map; a later GitHub-hosted DAST run is recorded as successful in `evidence/github-security-runs-2026-10-06.md`. | `evidence/deployment-security-retest-2026-10-03.md`, `evidence/owasp-top-10-2025-review.md`, `evidence/ci-cd.md` |

The team remains responsible for reviewing generated work and validating final claims.

## Licences and attribution

- No third-party application template or stock imagery is included. The three decorative site images are AI-generated (see the tools table); architecture diagrams use the AWS Architecture Icons listed above.
- Runtime libraries retain their respective upstream licences; primary direct Python dependencies are pinned in `analytics/requirements.txt` and `analytics/requirements-inference.txt`.
