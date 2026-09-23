# Infrastructure

Terraform provisions the AWS resources for the serverless application. The initial milestone creates:

- A private S3 frontend bucket
- A CloudFront distribution using Origin Access Control
- An API Gateway HTTP API
- A Python Lambda health endpoint
- A retained CloudWatch log group

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
```

## Cleanup

```bash
terraform destroy
```

CloudFront distributions can take several minutes to create, update, or delete.
