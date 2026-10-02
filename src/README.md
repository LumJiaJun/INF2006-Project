# Application source

Runnable frontend, backend, and Terraform infrastructure.

## Contents

- `frontend/`: static HTML, CSS, and JavaScript served through CloudFront
- `backend/`: focused Python Lambda handlers for health, analytics, prediction, and user history
- `infrastructure/`: Terraform for AWS resources
- `.env.example`: non-secret local defaults

## Local run instructions

Run the complete local website from the repository root:

```bash
pip install -r tests/requirements.txt
python src/local_server.py
```

This loopback-only server serves the real frontend and representative local
implementations of `GET /health`, `GET /analytics`, and `POST /predict`. It
derives the form schema from the deterministic synthetic sample model so the
browser workflow can be tested before Terraform deployment. It does not emulate
Cognito, DynamoDB history, Bedrock, WAF, CloudFront, VPC endpoints, or alarms.

Run the backend unit tests from the repository root:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Validate the infrastructure:

```bash
cd src/infrastructure
terraform init -backend=false
terraform fmt -check
terraform validate
terraform plan
```
