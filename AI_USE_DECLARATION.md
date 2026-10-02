# AI Use Declaration

Declare all AI tools and external baselines used, where they were used, the
verification the team performed, and any licences/attribution.

## Tools used

| Tool | Where it was used | Purpose |
|------|-------------------|---------|
| OpenAI Codex | `AGENTS.md`, `.gitignore`, `README.md`, `src/`, `tests/`, `evidence/`, and `project_manifest.yaml` | Repository inspection, implementation support, Terraform configuration, tests, documentation, and deployment verification. |
| Amazon Bedrock Claude Haiku 4.5 | Deployed `POST /chat` application feature | Answers authenticated, project-scoped user questions through a bounded prompt and response interface. |

## Sources and baselines

| Source / baseline | URL | Licence | Modifications made by the team |
|-------------------|-----|---------|--------------------------------|
| Airbnb Listings & Reviews dataset | https://www.kaggle.com/datasets/mysarahmadbhat/airbnb-listings-reviews/data | CC0 1.0 Public Domain | Profiled data quality, selected features, created a reproducible model pipeline, built a Glue transform, and exposed constrained aggregate analytics. |
| scikit-learn | https://scikit-learn.org/ | BSD-3-Clause | Used standard preprocessing and regression estimators; project-specific training, evaluation, validation, and deployment code is maintained in `analytics/` and `src/backend/predict/`. |

## Verification performed

| Area | Team verification | Evidence |
|------|-------------------|----------|
| Repository and Terraform | Ran 37 unit tests, the loopback frontend/API smoke journey, JavaScript syntax checks, `terraform fmt -check`, `terraform validate`, and the earlier post-apply no-change plans. | `evidence/local-development-2026-10-02.md`, `evidence/verification-2026-09-30.txt`, `evidence/verification-2026-10-01.txt` |
| Live application | Ran the deployed smoke script for frontend assets and headers, health, prediction, ten-city analytics, anonymous authorization rejection, and malformed input. | `evidence/verification-2026-09-30.txt`, `evidence/test-functional.md` |
| Data and model | Reproduced profiling, training metrics, Glue transformation, Parquet output, Athena scan size, and ten-city response. | `evidence/test-data-ai.md`, `evidence/data-pipeline.md` |
| Authentication and AI | Completed a consented Cognito journey and separate Bedrock-plus-DynamoDB integration check without retaining credentials, codes, tokens, or prompts. | `evidence/test-functional.md`, `evidence/test-security.md` |
| Storage and IAM | Checked S3 public-access controls, direct-access denial, DynamoDB PITR, claim-derived history access, and selected allowed and denied IAM actions. | `evidence/test-security.md`, `evidence/threat-control-map.md` |
| Monitoring | Triggered and reset the prediction alarm, observed successful encrypted SNS publication, and received the operator email. | `evidence/monitoring.md` |
| Load and resilience | Retained both successful bounded tests and the earlier quota-related 503 result; the approved-quota retest produced only HTTP 200 and controlled HTTP 429 responses. | `evidence/test-web-load.md`, `evidence/test-resilience.md` |
| CI security | Checked successful CI, CodeQL, dependency audit, Bandit, and a corrected pinned local ZAP run; the GitHub DAST rerun remains explicitly unclaimed. | `evidence/ci-cd.md`, `evidence/verification-2026-09-30.txt` |

The team remains responsible for reviewing generated work and validating final claims.

## Licences and attribution

- No third-party application template or visual asset is included.
- Runtime libraries retain their respective upstream licences; primary direct Python dependencies are pinned in `analytics/requirements.txt` and `analytics/requirements-inference.txt`.
