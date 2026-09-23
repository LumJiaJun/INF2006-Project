# AI Use Declaration

Declare all AI tools and external baselines used, where they were used, the
verification the team performed, and any licences/attribution.

## Tools used

| Tool | Where it was used | Purpose |
|------|-------------------|---------|
| OpenAI Codex | `AGENTS.md`, `.gitignore`, `README.md`, `src/`, `tests/`, `evidence/`, and `project_manifest.yaml` | Repository inspection, implementation support, Terraform configuration, tests, documentation, and deployment verification. |

## Sources and baselines

| Source / baseline | URL | Licence | Modifications made by the team |
|-------------------|-----|---------|--------------------------------|
| Airbnb Listings & Reviews dataset | https://www.kaggle.com/datasets/mysarahmadbhat/airbnb-listings-reviews/data | CC0 1.0 Public Domain | Profiled data quality, selected features, created a reproducible model pipeline, built a Glue transform, and exposed constrained aggregate analytics. |
| scikit-learn | https://scikit-learn.org/ | BSD-3-Clause | Used standard preprocessing and regression estimators; project-specific training, evaluation, validation, and deployment code is maintained in `analytics/` and `src/backend/predict/`. |

## Verification performed

- Reviewed the Terraform plan before each apply and confirmed that it contained no destructive actions.
- Ran `terraform fmt -check`, `terraform validate`, Python unit tests, and JavaScript syntax checking.
- Verified the deployed CloudFront frontend, API workflows, CORS restriction, direct S3 denial, Cognito-protected routes, Glue output, Athena query, DynamoDB recovery setting, alarms, and CloudWatch log events.
- Compared generated documentation claims against dated command output in `evidence/` and retained failed stress-test findings.
- The team remains responsible for reviewing future generated work and validating all final claims.

## Licences and attribution

- No third-party application template or visual asset is included.
- Runtime libraries retain their respective upstream licences; primary direct Python dependencies are pinned in `analytics/requirements.txt` and `analytics/requirements-inference.txt`.
