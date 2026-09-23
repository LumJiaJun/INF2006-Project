# Infrastructure

Terraform provisions the AWS resources for the serverless application. The initial milestone creates:

- A private S3 frontend bucket
- A CloudFront distribution using Origin Access Control
- An API Gateway HTTP API
- A Python Lambda health endpoint
- A retained CloudWatch log group
- An encrypted ECR repository for the prediction Lambda image

## Prerequisites

- Terraform 1.6 or newer
- AWS credentials available through the standard AWS credential chain
- Permission to create the resources declared in this directory

Do not place AWS access keys in Terraform variables or files.

## Validate

```bash
terraform init -backend=false
terraform fmt -check
terraform validate
terraform plan
```

## Deploy

```bash
terraform apply
terraform output frontend_url
terraform output health_url
terraform output prediction_ecr_repository_url
terraform output cognito_hosted_ui_url
terraform output prediction_history_url
```

The browser uses Cognito's authorization-code flow with PKCE. Public predictions use `/predict`; signed-in predictions use `/predictions` and are saved to DynamoDB for retrieval from `/history`.

After changing frontend files, invalidate CloudFront so cached objects are refreshed:

```powershell
$distributionId = terraform output -raw cloudfront_distribution_id
aws cloudfront create-invalidation --distribution-id $distributionId --paths "/*"
```

## Build prediction image

Run from the repository root after recreating `analytics/artifacts/airbnb_price_model.joblib`:

```powershell
$imageTag = "1.0.3"
$repositoryUrl = terraform -chdir=src/infrastructure output -raw prediction_ecr_repository_url
$registry = $repositoryUrl.Split('/')[0]

docker build --platform linux/amd64 --provenance=false `
  -f src/backend/predict/Dockerfile `
  -t "airbnb-prediction:$imageTag" .

aws ecr get-login-password --region ap-southeast-1 |
  docker login --username AWS --password-stdin $registry
docker tag "airbnb-prediction:$imageTag" "${repositoryUrl}:$imageTag"
docker push "${repositoryUrl}:$imageTag"
```

Provenance is disabled because Lambda requires a single-architecture image manifest. ECR tags are immutable, so use a new tag whenever image content changes.

## Cleanup

```bash
terraform destroy
```

CloudFront distributions can take several minutes to create, update, or delete.
