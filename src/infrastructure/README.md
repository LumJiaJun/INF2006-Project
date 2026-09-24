# Infrastructure

Terraform provisions the AWS resources for the serverless application, identity, application data, and analytical data path:

- A private S3 frontend bucket
- A CloudFront distribution using Origin Access Control
- An API Gateway HTTP API
- A Python Lambda health endpoint
- A retained CloudWatch log group
- An encrypted ECR repository for the prediction Lambda image
- A Cognito user pool and DynamoDB prediction-history table
- A private encrypted S3 data lake, Glue transform, catalog table, and Athena workgroup
- A fixed-query analytics Lambda and `GET /analytics` route
- A separate Claude Haiku chat Lambda and Cognito-protected `POST /chat` route
- CloudWatch alarms and dashboard with an encrypted SNS action topic

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
terraform output data_lake_bucket_name
terraform output glue_transform_job_name
terraform output analytics_url
terraform output chat_url
terraform output operations_dashboard_name
terraform output operational_alerts_topic_arn
```

The browser uses Cognito's authorization-code flow with PKCE. Public predictions use `/predict`; signed-in predictions use `/predictions` and are saved to DynamoDB for retrieval from `/history`. Signed-in users can call `/chat`; the separate AI Lambda uses the global Claude Haiku 4.5 inference profile, a 220-token output cap, and a tighter one-request-per-second API route limit.

After changing frontend files, invalidate CloudFront so cached objects are refreshed:

```powershell
$distributionId = terraform output -raw cloudfront_distribution_id
aws cloudfront create-invalidation --distribution-id $distributionId --paths "/*"
```

## Run the data pipeline

The raw data is not managed by Terraform or committed to Git. From the repository root, upload the supplied listing file and start the deployed transform:

```powershell
$bucket = terraform -chdir=src/infrastructure output -raw data_lake_bucket_name
$job = terraform -chdir=src/infrastructure output -raw glue_transform_job_name

aws s3 cp "data/raw/Airbnb Data/Listings.csv" `
  "s3://$bucket/raw/listings/Listings.csv" --sse AES256
aws glue start-job-run --job-name $job
```

The job is limited to two `G.1X` workers, a ten-minute timeout, and no retries. Athena queries run in a workgroup with enforced encrypted output, CloudWatch metrics, a 1 GiB scan cutoff, and seven-day query-result expiry.

## Monitoring

CloudWatch alarms track API 5xx responses, prediction/analytics/chat Lambda errors, and health throttles. The dashboard gives the chat Lambda its own duration and error series so AI latency can be reviewed independently. Their SNS topic uses a rotating customer-managed KMS key whose policy permits only this account's named CloudWatch alarms to publish. No subscription is committed because recipient addresses are personal deployment configuration. Add and confirm an operator endpoint separately before treating the topic as a complete notification channel.

The development account has a Lambda concurrency quota of 10, so the API stage uses a conservative two-request burst and two-request-per-second limit. See `evidence/test-resilience.md` for passing expected-load results and the honestly recorded higher-concurrency failure.

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
