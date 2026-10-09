# Airbnb Pricing and Market Intelligence Platform

## Problem statement

Prospective and existing Airbnb hosts lack a simple way to estimate an appropriate nightly price and understand the surrounding market before listing or evaluating a property for hosting. Existing listing pages do not combine model-based scenario estimation, local market analytics, comparison of potential configurations, and private prediction history in one focused workflow. This platform helps users explore listing configurations and historical market patterns before deciding whether hosting may suit a property. It provides decision support, not property valuation, purchase advice, guaranteed demand, or predicted investment return.

## Team members

| Name | Student ID | Role |
|------|-----------|------|
| Lum Jia Jun | 2500022 | Cloud Alternatives and Portability Reviewer |
| Nixon Lee Disheng | 2500594 | Infrastructure and Cloud Deployment Lead |
| Madugula Adheesh | 2500670 | Application and Data Prototype Contributor |
| Leow Yi Hao Ignatius | 2501538 | Application QA and Presentation Reviewer |
| Wong Zhen Ho Brendan | 2503427 | Frontend Navigation and Test Contributor |

## Deployment status

The development stack was rebuilt in `ap-southeast-1` on 2026-10-06 from a
reviewed Terraform plan containing 124 creates, 0 changes, and 0 destroys. The
full-data model replay matched exactly, the Glue transform succeeded, the
redacted cloud verifier passed across 148 Terraform resources with zero drift,
and a live bounded Claude Haiku call returned HTTP 200. The live site on 7 October 2026 is https://dqvmcy3nxs3v.cloudfront.net (CloudFront domain; it stays the same across in-place `terraform apply` updates but changes if the stack is destroyed and recreated). Run
`terraform -chdir=src/infrastructure output -raw frontend_url` for the current
public URL if this link does not load. AWS now reports the operator-managed SNS email subscription as
confirmed; the recipient address remains deployment configuration rather than
source-controlled data. See
`evidence/cloud-verification-2026-10-06.md` and
`evidence/aws-pricing-calculator-2026-10-06.md`.

## Documentation map

The root README is the marker entry point. Use the following paths for the
complete instructions behind each workflow:

| Need | Start here |
|------|------------|
| Reproduce and inspect the project without AWS | Steps 1-4 below |
| Recreate, verify, and destroy the AWS environment | `src/infrastructure/README.md` |
| Run focused local, cloud, load, security, and chatbot tests | `tests/README.md` |
| Obtain and verify the full dataset | `data/README.md` |
| Reproduce the analytics and ML pipeline | `analytics/README.md` |
| Work safely with shared Terraform state | `TEAM_WORK_GUIDE.md` |
| Trace claims to dated artefacts | `evidence/README.md` and `project_manifest.yaml` |

The offline path is the default for marking. Cloud steps are optional,
authorized-operator procedures because cloud recreation and continued uptime
incur cost.

## Reproduce from a clean machine

The marker-friendly path below reproduces the application, tests, sample ML
pipeline, and Terraform validation without an AWS account. It uses committed
synthetic data, creates only ignored local files, has no cloud cost, and does
not require any credentials.

### Prerequisites

| Path | Requirements |
|------|--------------|
| Complete offline reproduction | Git, Python 3.11 or newer, Node.js 24, and Terraform 1.10 or newer |
| Optional full-data model replay | The CC0 `Listings.csv` source described in `data/README.md` |
| Optional AWS recreation | AWS CLI v2, Docker, authorized AWS credentials, the full model artefact, and the encrypted Terraform backend |

Internet access is needed on a new machine to clone the repository, install
Python packages, and download Terraform providers. The application itself does
not make an external request during the offline preflight.

### 1. Clone and prepare

```bash
git clone https://github.com/LumJiaJun/INF2006-Project.git
cd INF2006-Project
python -m venv .venv
```

Activate the environment with `.\.venv\Scripts\Activate.ps1` in PowerShell or
`source .venv/bin/activate` on macOS/Linux, then run:

```bash
python -m pip install --upgrade pip
python -m pip install -r tests/requirements.txt
terraform -chdir=src/infrastructure init -backend=false
```

`-backend=false` downloads the pinned providers for validation without reading
or creating cloud state. Do not run `terraform apply` from this initialization.

### 2. Run the automated offline reproduction

```bash
python tests/local_preflight.py --include-ml
```

A successful run:

1. Executes the Python unit suite.
2. Compiles the Python source and validates every manifest path.
3. Syntax-checks the frontend JavaScript with Node.js.
4. Runs `terraform fmt -check -recursive` and `terraform validate`.
5. Trains and evaluates a deterministic model on the committed 500-row sample.
6. Starts an ephemeral local server and verifies the frontend, health,
   analytics, model-schema, and prediction routes over HTTP.

The final line must be `Local preflight completed successfully.` The last
recorded clean run passed 53 tests and validated 17 manifest paths. Generated
models, metrics, caches, and Terraform provider files remain in ignored paths.

### 3. Inspect the application locally

```bash
python src/local_server.py
```

Open `http://127.0.0.1:8000`, confirm that the header says `Local demo`, view
the dashboard and market analytics, submit one estimator scenario, and compare
the returned estimate and scenario cards. Stop the server with `Ctrl+C`.

Local mode serves the real frontend and prediction handler with deterministic
synthetic data. Cognito sign-in, private DynamoDB history, Bedrock chat,
CloudFront, WAF, VPC endpoints, alarms, and other managed-service controls are
deliberately disabled rather than falsely simulated.

### 4. Replay the full-data model when the source is available

Download the CC0 dataset from the source in `data/README.md`, place its listing
file at `data/raw/Airbnb Data/Listings.csv`, verify the documented SHA-256, and
run:

```bash
python tests/verify_full_model.py --listings "data/raw/Airbnb Data/Listings.csv"
```

Success means the selected model, candidate metrics, dataset counts, model
size, and model SHA-256 exactly match the committed evaluation. The raw dataset
and generated model stay outside Git because of their size; this external file
is the only unavoidable prerequisite for the full-data replay.

### 5. Recreate the AWS environment only when authorized

The assessed application stack is currently live from the verified 6 October
deployment. An authorized team operator can recreate it by following the
ordered state, model-image, deployment, data-pipeline, verification, and cleanup
commands in `src/infrastructure/README.md`. Never commit credentials,
`backend.hcl`, plan files, Terraform state, the raw dataset, or generated model
artefacts.

Cloud operation incurs charges, particularly for the two-AZ interface
endpoints and WAF. The saved AWS Pricing Calculator workload estimate is about
$72.12 per continuously deployed month before discounts and tax; the planning
total is about $72.92 after the stated Haiku token scenario. Review
`evidence/aws-pricing-calculator-2026-10-06.md`, configure a budget, and destroy
temporary resources promptly.
For team handoff and state safety, also read `TEAM_WORK_GUIDE.md`.

After deployment, `tests/verify_cloud.ps1` performs a zero-drift plan, public
smoke workflow, and checks of Lambda state, private-subnet attachment, alarms,
CloudTrail, DynamoDB recovery, Glue, S3 public-access blocks, CloudFront WAF,
and SNS subscription status. Its generated Markdown excludes cloud identifiers,
URLs, operator addresses, tokens, and credentials.

## Architecture

![Current architecture diagram](evidence/architecture-current.png)

The diagram above (editable source: `evidence/architecture-full.drawio`) shows the
global edge (WAF, CloudFront, private S3), Cognito and the API Gateway JWT
authorizer, the five Lambda functions in two private subnets across two
availability zones, the `lambda` and `vpc-endpoints` security groups, gateway
and interface endpoints, DynamoDB, Bedrock, the Athena, Glue and S3 analytics
path, observability and audit services, and the GitHub Actions CI/CD lane with
Terraform. It deliberately does not show AgentCore, ALB, NAT Gateway, containers,
or third-party identity services because those components are not deployed in
this project. The earlier
[detailed trust and service-flow diagram](evidence/architecture-detailed.png)
remains in the evidence folder as a supplementary view; where the two differ,
the diagram above and the Terraform in `src/infrastructure` are authoritative.

CloudFront serves a static frontend from a private S3 origin. The frontend calls an API Gateway HTTP API, which invokes focused Lambda functions. `GET /health`, `POST /predict`, and `GET /analytics` are public. Cognito protects `POST /predictions`, `GET /history`, and the Claude Haiku-backed `POST /chat` route. AI traffic uses a separate Lambda and tighter route throttle so it can be cost-controlled independently from prediction traffic. The assistant receives a compact server-controlled set of verified platform facts and only the signed-in user's ten latest DynamoDB prediction records; DynamoDB is not treated as a general knowledge base. History is explicitly ordered newest first, mixed-currency comparisons are blocked, model temperature is zero, and plain-text output is bounded to 120 words. Authenticated predictions retain the safe listing and host signals needed for useful follow-up questions while excluding coordinates. The estimator also offers bounded what-if predictions for amenities, guest capacity, and superhost status; these are model scenarios, not future-price forecasts. The evaluated model runs from an ECR-backed Lambda container. Glue converts the raw listing CSV into city-partitioned Parquet in a separate private S3 data lake, and the analytics Lambda runs a fixed aggregate query through Athena.

The current Terraform design configures all five Lambda functions with private subnets across two availability zones. It uses S3 and DynamoDB gateway endpoints plus private interface endpoints for CloudWatch Logs, Athena, and Bedrock Runtime in both AZs. There is deliberately no NAT Gateway: the functions only require the AWS services covered by those endpoints. DynamoDB remains an AWS-managed regional service rather than a resource placed inside the customer VPC. The diagram shows the two logical DynamoDB tables (history and idempotency) as separate icons outside the AZ boxes, and AWS replicates each table across three AZs in the Region; no duplicate table per subnet is required. Each interface endpoint is drawn once at VPC level although it has a network interface in each AZ. This provides in-Region availability, not cross-Region failover. See `evidence/availability-review-2026-10-06.md` and `evidence/aws-serverless-reference-review-2026-09-28.md`. CloudFront is protected by a global WAF ACL, and a regional management CloudTrail writes validated logs to a dedicated S3 bucket; see `evidence/edge-security-2026-09-29.md`.

Cognito uses email verification, a strong password policy, authorization-code flow with PKCE, token revocation, and required TOTP authenticator-app MFA. The application never handles passwords or MFA secrets.

### Database choice: DynamoDB instead of RDS

The brief requires a persistent cloud storage or database layer with a defined
data model; it does not require a relational database. The project uses each
store for a measured access pattern rather than adding services for diagram
complexity:

| Requirement | Implemented store and reason |
|-------------|------------------------------|
| Save a prediction for one authenticated user | DynamoDB writes one item under the verified Cognito `sub` partition key. |
| Retrieve that user's newest predictions | DynamoDB queries `user_id` plus the time-ordered `created_at_prediction_id` sort key without a scan or join. |
| Deduplicate an authenticated retry | A separate DynamoDB table uses `user_id` plus `idempotency_key` and expires records through TTL. |
| Run aggregate market SQL over the listing dataset | S3, Parquet, Glue Catalog, and Athena keep analytical queries out of the transactional history table. |
| Handle low, uneven development traffic | DynamoDB on-demand avoids an always-running database instance and capacity planning. |

RDS or Aurora would be justified if the scope added related booking, payment,
host, property, and availability records that require joins, foreign keys, or
multi-record ACID transactions. None of those requirements exists in the
implemented estimator and private-history workflow. Adding RDS now would
duplicate persistence, introduce connection and schema-migration operations,
raise the cost floor, and weaken the purpose-built serverless rationale without
solving a user problem. This decision follows AWS guidance to choose storage by
access pattern; see the
[AWS Lambda database decision guide](https://docs.aws.amazon.com/lambda/latest/dg/ddb-rds-database-decision.html)
and the [AWS Well-Architected purpose-built data-store guidance](https://docs.aws.amazon.com/wellarchitected/latest/framework/perf_data_use_purpose_built_data_store.html).

## Technology list

- Cloud provider: AWS
- Compute/deployment: API Gateway and AWS Lambda, provisioned with Terraform
- Networking: two-AZ private Lambda VPC with S3/DynamoDB gateway endpoints and Logs/Athena/Bedrock interface endpoints
- Frontend: private Amazon S3 origin and Amazon CloudFront
- Identity and data: branded Cognito Managed Login v2 and encrypted Amazon DynamoDB prediction history
- Data engineering: private Amazon S3 data lake, AWS Glue, Parquet, Glue Data Catalog, and Amazon Athena
- Operations: CloudWatch structured logs, metrics, dashboard and alarms with an encrypted SNS action topic
- Delivery: GitHub Actions CI/CD, CodeQL SAST, OWASP ZAP DAST, and a manual-dispatch OIDC deployment workflow designed for environment approval
- Analytics / AI-ML: reproducible scikit-learn price regression pipeline plus a bounded Amazon Bedrock Claude Haiku 4.5 assistant
- Application: HTML, CSS, JavaScript, and Python

### Cloud service-model classification

- Deployment model: AWS public cloud in `ap-southeast-1`.
- FaaS: five AWS Lambda functions provide request-driven compute without managed servers.
- Managed PaaS/serverless data and application services: API Gateway, S3, DynamoDB, Cognito, Glue, Athena, Bedrock, CloudFront, WAF, CloudWatch, SNS, and KMS.
- IaaS networking: the team configures the VPC, two private subnets, route tables, security groups, and VPC endpoints, but no EC2 virtual machines are operated.
- SaaS delivery tooling: GitHub and GitHub Actions host source control and CI/CD outside the AWS runtime.
- Container packaging, not CaaS: ECR stores the Lambda inference image; ECS, EKS, Fargate, and Kubernetes are not used.

These labels describe responsibility boundaries rather than claiming that every managed AWS product fits only one service-model category.

## Analytics decision flow

The interface presents four bounded forms of analysis without overstating what
the cross-sectional dataset supports:

1. **Descriptive:** Athena returns listing count, average and median nightly
   price, and average rating for each city.
2. **Diagnostic:** the same governed query reports average-to-median shape,
   capacity-price correlation, and the observed superhost/non-superhost price
   difference. These are associations, not evidence that a feature causes a
   price change.
3. **Predictive:** the evaluated regression pipeline estimates a nightly price
   for a validated listing scenario and reports its local currency and model
   scope.
4. **Prescriptive:** the browser compares that estimate with the same-city
   historical median and suggests a cautious next comparison. It does not
   recommend an investment, promise demand, or optimize profit.

`data/sample/listings_synthetic.csv` and `python tests/local_preflight.py
--include-ml` provide a safe offline reproduction path. Synthetic-sample
metrics prove code execution only; the report uses the evaluated full-dataset
metrics.

## CI/CD and shared state

Pull requests and pushes to `main` or `nixon` run unit tests, Python compilation,
frontend syntax checks, secret-pattern checks, Terraform formatting and
validation. The security gates additionally run pinned dependency audits for
the application and analytics requirements plus Bandit Python static analysis;
CodeQL SAST covers Python and JavaScript. Deployment is manual,
requires typing `DEPLOY`, and is gated by the GitHub `development` environment.
The `Deploy development` workflow accepts only `main` or `nixon`, repeats the
application and Terraform validation before assuming AWS access (it does not
wait for the CodeQL or security-gate workflows to pass on that revision), and targets
the GitHub `development` environment before it can apply the reviewed plan.
Required reviewers must be configured in the repository environment settings
before claiming human approval enforcement. The workflow uses GitHub OIDC
rather than stored AWS access keys.

After a successful deployment, OWASP ZAP DAST performs a passive baseline scan.
It can also be started manually. The scan accepts only HTTPS and requires the
target hostname to exactly match the allowlisted host, uploads HTML, JSON, and
Markdown reports, and fails on scanner errors plus new or explicitly actionable
findings. Narrowly accepted static-site findings are documented in
`.zap/rules.tsv` and must not be broadened without review.
Configure `AWS_DEPLOY_ROLE_ARN`, `TF_STATE_BUCKET`, `TF_STATE_KMS_KEY_ARN`,
`MODEL_ARTIFACT_S3_URI`, `ALERT_EMAIL`, `DAST_TARGET_URL`, and
`DAST_ALLOWED_HOST` in the protected GitHub environment before using deployment
or DAST. `ALERT_EMAIL` must contain the confirmed operator address so an
automated deployment preserves the Terraform-managed SNS subscription.

To deploy, open GitHub Actions, select `Deploy development`, choose `nixon` or
`main`, and type `DEPLOY`. Configure required reviewers in the `development`
environment first so GitHub pauses before the AWS apply step. The OIDC role
trust policy must allow only this repository and the `development` environment;
do not replace this with long-lived AWS access keys.

The state bootstrap under `src/infrastructure/bootstrap` manages a private,
versioned S3 bucket encrypted with a rotating customer-managed KMS key. S3
lockfiles provide concurrency control. Terraform state is not stored in KMS or
Secrets Manager and no state, account ID, key ARN, or backend file is committed.

CloudFront already provides HTTPS on its generated domain using an AWS-managed
certificate. ACM becomes useful only after the team owns a custom domain and
can complete DNS validation, so a custom certificate remains pending until
those domain details are supplied.

## Submission packaging

After committing the reviewed final files, create the marker ZIP from tracked
content rather than compressing the working directory. This excludes ignored
Terraform state, credentials, raw data, local caches, logs, and test output:

```bash
git archive --format=zip --output=../Group_G014_INF2006_Project.zip HEAD
```

Open the ZIP before submission and confirm that `README.md`,
`project_manifest.yaml`, `report.pdf`, `src/`, `data/`, `analytics/`,
`evidence/`, `tests/`, `TEAM_CONTRIBUTIONS.md`, and
`AI_USE_DECLARATION.md` are directly under the ZIP root.

## Known limitations

- A consented single-account browser journey covering sign-up, verification, TOTP MFA, prediction save, history retrieval, and protected chat is recorded in `evidence/test-functional.md`. The deployed chatbot evaluator now proves owner-versus-other-user DynamoDB partition isolation with two synthetic identities, but a full two-browser Cognito journey remains future work.
- Analytics reports an average-to-median market-shape ratio for within-city price skew. Cities retain their different local currencies and must not be ranked on one currency scale. User-currency conversion is intentionally disabled because the dataset has no timestamped exchange-rate source.
- The dataset is a cross-sectional listings snapshot, not a price or demand time series. It supports listing-price estimation, descriptive summaries, and bounded diagnostic associations, not causal conclusions, future-price forecasting, or condition monitoring.
- The evaluated model has material error and supports only the typical 99% price range learned per city.
- A prediction cold start was measured at approximately 3.3 seconds with 2 GB Lambda memory in the initial manual check. A first request immediately after the 2026-10-03 clean rebuild exceeded the API response window, returned HTTP 503, and then completed in Lambda; the browser now retries one transient 502/503/504 response while showing a model-warming state.
- The development AWS account Lambda concurrency quota is now 1,000. API Gateway still throttles excess traffic, and bounded stress results are recorded in `evidence/test-resilience.md`.
- Authenticated prediction retries now use a server-side idempotency key; a separate cross-region recovery exercise remains future work.
- The chatbot's 24-scenario local evaluation and latest 26-scenario deployed evaluation check factual grounding, exact history and dates, arithmetic, currency handling, authentication boundaries, privacy, injection, causal overclaiming, unsupported transactions, market grounding, and scope. They do not prove correctness for every possible question or future managed-model revision.
- Cloud deployment requires an AWS account. The current full architecture is estimated at about $72.92 per continuously deployed month before discounts and tax, dominated by two-AZ interface endpoint hours.
- Cost assumptions and EC2 comparisons are documented in `evidence/cost-estimate.md`. The historical $4-$7 estimate predates the two-AZ interface endpoints and WAF and is not the current full-stack estimate; the saved calculator result and redacted line items are in `evidence/aws-pricing-calculator-2026-10-06.md`.
- No managed threat detection service (GuardDuty, Security Hub) is enabled. Detection relies on CloudTrail, CloudWatch alarms, and the preventive controls described above.
- Saved-prediction retries are deduplicated only when the browser reuses the same idempotency key. A stalled attempt becomes retryable after a 60 second lease; a genuinely new submission, or a reused key after the 24 hour record expiry, creates a new history record.
