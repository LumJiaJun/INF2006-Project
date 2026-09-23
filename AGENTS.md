# INF2006 Project Working Instructions

These instructions apply to the entire repository. They preserve the agreed project direction for future contributors and coding agents.

## Project Goal

Build a serverless Airbnb Pricing and Market Intelligence Platform on AWS for the SIT INF2006 Cloud Computing and Big Data team project.

The core user capabilities are:

1. Estimate an Airbnb nightly price using a real evaluated ML pipeline.
2. Explore market analytics supported by the actual dataset.
3. View prediction history for the authenticated user.

Treat every prediction as an estimate. Do not claim that it is an objectively correct market price.

## Source of Truth

- Follow the official INF2006 project brief and preserve its required submission structure.
- Keep `project_manifest.yaml` fields and required relative paths intact.
- Use the actual dataset and data dictionary before selecting features or analytics.
- Do not fabricate dataset fields, model performance, scalability, security, reliability, or deployment results.
- Reviews data may not contain review text. Do not add sentiment analysis without evidence that the data supports it.
- Availability is not the same as demand. Describe any proxy and its limitations accurately.

## Target Architecture

Prefer a clear serverless AWS design:

- Frontend: private S3 origin served through CloudFront.
- API: API Gateway.
- Compute: focused Lambda functions for health, prediction, analytics, and history.
- Authentication: Cognito for protected user functionality.
- Application records: DynamoDB, designed from access patterns.
- Data lake: S3 paths for raw, processed, model, and analytics artefacts.
- Data engineering: Glue and Parquet when the core application is stable.
- Analytics: Glue Data Catalog and Athena with approved queries only.
- ML: offline reproducible training and Lambda inference when technically practical.
- Observability: CloudWatch logs, metrics, alarms, and SNS where justified.
- Infrastructure: Terraform for reproducible provisioning and teardown.

Do not add EC2, Auto Scaling Groups, nginx, ECS, Fargate, EKS, Kubernetes, RDS, Redis, OpenSearch, Step Functions, EventBridge, SQS, WAF, SageMaker, Bedrock, AgentCore, a VPC, NAT Gateway, or Route 53 unless a measured requirement justifies it first.

The optional AI assistant is not on the V1 critical path. Do not turn the service into a generic chatbot.

## Delivery Order

Work in small, testable milestones:

1. Private S3 frontend, CloudFront, API Gateway, Lambda `GET /health`, and CloudWatch logs.
2. Inspect the real dataset, document provenance, and build reproducible EDA and preprocessing.
3. Train and evaluate a baseline and candidate price model using MAE, RMSE, and R-squared.
4. Add `POST /predict` using the exported preprocessing and model pipeline.
5. Add DynamoDB prediction persistence and user history.
6. Add Cognito and enforce user-scoped authorization.
7. Add supported market analytics, then Glue, Parquet, and Athena.
8. Add monitoring, alarms, security tests, load tests, resilience tests, and recreation evidence.
9. Consider AgentCore only after the core project is stable.

Do not implement the full architecture in one change. The core prediction workflow takes priority over optional services.

## Engineering Rules

- Inspect existing code and instructions before changing files.
- Preserve the required repository structure and existing working code.
- Make the smallest reasonable change for the current milestone.
- Use a lightweight HTML, CSS, and JavaScript frontend unless a real need for a framework emerges.
- Keep APIs small and purposeful. Validate requests at the client and backend boundaries.
- Return appropriate HTTP status codes and safe JSON errors without stack traces or internal details.
- Keep Lambda responsibilities focused without creating decorative microservices.
- Use complete, reusable ML preprocessing and model pipelines to avoid training-serving skew.
- Keep AWS costs low and document assumptions, limits, alternatives, and trade-offs.
- Use ASCII punctuation. Do not use emojis or em dashes in repository content or commit messages.
- Avoid formatting-only changes and unrelated renames.

## Security Rules

- Apply least privilege with purpose-specific IAM permissions and scoped resources.
- Use HTTPS, encryption at rest, input validation, authorization, and secure S3 access.
- Derive a history user's identity from validated authentication claims, never from a caller-supplied user ID.
- Do not accept arbitrary Athena SQL from users.
- Do not expose credentials, tokens, secrets, stack traces, internal paths, or sensitive logs.
- Never commit `.env` files, credentials, private keys, tokens, Terraform state, sensitive variable files, large raw datasets, or unnecessary generated model artefacts.
- Use IAM roles and normal AWS credential resolution. Never place AWS access keys in Terraform variables or source code.
- Review staged changes for secret-like content before every commit.

## Validation and Evidence

Test each meaningful stage and report failures honestly. Where applicable, run:

- `terraform fmt -check`
- `terraform validate`
- `terraform plan`
- focused application and unit tests
- functional, validation, security, ML, scalability, resilience, and infrastructure recreation tests

Do not claim AWS deployment, model accuracy, or test success unless it was actually observed.

Store dated, redacted, reproducible evidence under `evidence/`. Prefer commands, logs, and exported configuration over screenshots alone. Never include AWS account IDs, credentials, personal data, token-bearing URLs, or proprietary data in evidence.

## Git Discipline

- Work on the `nixon` branch unless the user explicitly requests another branch.
- Use multiple meaningful commits that reflect genuine working milestones.
- Before each commit, inspect status, diff, staged files, test results, and possible secrets.
- Stage explicit files. Do not use `git add .` blindly.
- Do not create fake progression by splitting trivial changes.
- Do not force push, rewrite shared history, amend other contributors' commits, or use destructive resets.
- Leave the repository working after every significant milestone where practical.
- If identity, permissions, remote access, or branch protection prevents committing, stop and report it.

## Documentation

Keep `README.md`, `project_manifest.yaml`, evidence, data documentation, analytics reproduction instructions, AI-use declaration, and team contributions factual and synchronized with implementation.

The final README must explain purpose, architecture, prerequisites, local development, ML training, Terraform deployment, testing, cleanup, and known limitations. Commands must be real and must not be described as tested unless they were run.
