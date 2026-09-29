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

- **Terraform and state:** Reviewed the plan before each apply and confirmed that the deployment contained no destructive actions. The final infrastructure plan reported no drift. Terraform formatting, provider validation, and the encrypted remote-state bootstrap configuration were checked.
- **Frontend S3 bucket:** Created a private, versioned, encrypted S3 bucket for the static site, enabled Block Public Access and bucket ownership controls, uploaded the HTML, CSS, JavaScript, configuration, model-options, and local image assets, and verified that direct S3 access was denied.
- **CloudFront:** Created the distribution with an Origin Access Control to the private frontend bucket, HTTPS viewer redirection, security response headers, and the default root object. The deployed CloudFront URL returned HTTP 200 and the cache was invalidated after deployment.
- **API Gateway:** Created the regional HTTP API, default stage, Lambda integrations, access logging, CORS allow-list, and routes for health, prediction, analytics, history, authenticated prediction, and chat. Public health, prediction, and analytics workflows were exercised; malformed input was rejected and protected routes returned HTTP 401 without a Cognito token.
- **Health Lambda:** Created the focused health function, execution role, log group, API integration, and throttling alarm. The live endpoint returned a healthy response and CloudWatch recorded a structured health event.
- **Prediction Lambda and ECR:** Created the container-image Lambda, scoped execution role, log group, API integrations, and error alarm. Built and pushed the evaluated model image to the immutable ECR repository, invoked the live prediction route successfully, and confirmed that ECR scanning completed with zero findings.
- **Analytics Lambda, Glue, and Athena:** Created the analytics function, Glue transform job, Glue catalog database/table, S3 raw and curated data paths, and Athena workgroup. Uploaded the listings dataset, ran the Glue transform to `SUCCEEDED`, queried the curated output, and confirmed the expected ten-city analytics response.
- **History and idempotency DynamoDB:** Created the encrypted prediction-history table with user-scoped access patterns and point-in-time recovery, plus the separate idempotency table with TTL. The recovery setting was inspected in the console and authenticated history/idempotency behavior was covered by the tests.
- **Cognito:** Created the user pool, email verification settings, application client, hosted domain, managed-login branding, and JWT authorizer. The protected API behavior and the consented sign-up, verification, TOTP MFA, prediction save, history, and chat journey were verified separately in the functional evidence.
- **Chat and Bedrock:** Created the chat Lambda, scoped role, log group, API route, and alarm. Invoked the deployed chat path with a project question and confirmed a bounded Claude Haiku response with unauthenticated access rejected at HTTP 401.
- **IAM and encryption:** Reviewed the purpose-specific Lambda, Glue, and application policies in the AWS Console and Terraform. Confirmed that the operational SNS topic uses a customer-managed rotating KMS key and that the state bucket uses encryption, versioning, and public-access blocking.
- **Monitoring and notification:** Created the CloudWatch log groups, operations dashboard, five alarms for API 5xx, prediction errors, analytics errors, chat errors, and health throttles, the encrypted SNS topic, and the confirmed school-email subscription. Set the prediction alarm to `ALARM`, received the SNS email, and reset the alarm to `OK`.
- **Quota and resilience:** Manually reviewed the approved Lambda account quota of 1,000 in the AWS Console. A controlled 100-request/10-worker health test and prediction test produced only HTTP 200 or expected API Gateway HTTP 429 responses, with no 5xx responses; CloudWatch showed no Lambda errors or Lambda-level throttles during the observation window.
- **Manual console review:** Cross-checked the command results in the AWS Console for Lambda quota and function state, API Gateway routes, Cognito configuration, S3 and CloudFront deployment status, Glue job completion, Athena output, DynamoDB point-in-time recovery, CloudWatch logs and alarms, SNS subscription confirmation, KMS key usage, and email delivery.
- Compared generated documentation claims against dated command output in `evidence/` and retained failed stress-test findings. The team remains responsible for reviewing future generated work and validating all final claims.
- The team remains responsible for reviewing future generated work and validating all final claims.

## Licences and attribution

- No third-party application template or visual asset is included.
- Runtime libraries retain their respective upstream licences; primary direct Python dependencies are pinned in `analytics/requirements.txt` and `analytics/requirements-inference.txt`.
