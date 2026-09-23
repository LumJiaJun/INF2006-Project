# Application source

Runnable frontend, backend, and Terraform infrastructure.

## Contents

- `frontend/`: static HTML, CSS, and JavaScript served through CloudFront
- `backend/`: focused Python Lambda handlers for health, analytics, prediction, and user history
- `infrastructure/`: Terraform for AWS resources
- `.env.example`: non-secret local defaults

## Local run instructions

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
