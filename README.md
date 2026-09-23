# Airbnb Pricing and Market Intelligence Platform

<!--
Entry point for the submission. Keep this concise and factual.
A marker should be able to understand the project and run safe, offline commands from here.
-->

## Problem statement

Airbnb hosts and prospective hosts can struggle to interpret local listing patterns and choose a reasonable nightly price. This project provides an estimated nightly price from listing characteristics, supported market analytics, and authenticated prediction history through a secure serverless AWS application. Predictions are estimates, not guaranteed market prices.

## Team members

| Name | Student ID | Role |
|------|-----------|------|
| <Name> | <ID> | <Role> |
| <Name> | <ID> | <Role> |
| <Name> | <ID> | <Role> |
| <Name> | <ID> | <Role> |

## Quickstart commands

```bash
# 1. Run offline unit tests
python -m unittest discover -s tests -p "test_*.py" -v

# 2. Initialise and validate Terraform
cd src/infrastructure
terraform init -backend=false
terraform fmt -check
terraform validate

# 3. Review and deploy the infrastructure
terraform plan
terraform apply

# 4. Show the deployed endpoints
terraform output frontend_url
terraform output health_url
```

## Architecture

![Architecture diagram](evidence/architecture.png)

CloudFront serves a static frontend from a private S3 origin. The frontend calls an API Gateway HTTP API, which invokes focused Lambda functions. `GET /health` and `POST /predict` are public. Cognito protects `POST /predictions` and `GET /history`; authenticated predictions are stored under the token-derived user identifier in an encrypted DynamoDB table. The evaluated model runs from an ECR-backed Lambda container.

## Technology list

- Cloud provider: AWS
- Compute/deployment: API Gateway and AWS Lambda, provisioned with Terraform
- Frontend: private Amazon S3 origin and Amazon CloudFront
- Identity and data: Amazon Cognito and encrypted Amazon DynamoDB prediction history
- Analytics / AI-ML: reproducible scikit-learn price regression pipeline with held-out evaluation
- Application: HTML, CSS, JavaScript, and Python

## Known limitations

- Market analytics dashboards and an analytical query layer are not implemented yet.
- Full sign-up, email verification, prediction save, and history retrieval require a manual browser test with a real email account.
- The evaluated model has material error and supports only the typical 99% price range learned per city.
- A prediction cold start was measured at approximately 3.3 seconds with 2 GB Lambda memory; warm calls were below 100 ms in the initial manual check.
- Cloud deployment requires an AWS account and may incur a small cost.
