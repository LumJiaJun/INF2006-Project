# Test: Security control

- **Objective:** Verify that users cannot bypass CloudFront to read frontend objects directly from S3 and that browser API access is restricted to the deployed frontend origin.
- **Setup:** Terraform-managed private frontend bucket, CloudFront Origin Access Control, and API Gateway CORS configuration.
- **Command / steps:**
  ```powershell
  $bucketName = terraform output -raw frontend_bucket_name
  $frontendUrl = terraform output -raw frontend_url
  $healthUrl = terraform output -raw health_url
  aws s3api get-public-access-block --bucket $bucketName
  Invoke-WebRequest -Uri "https://$bucketName.s3.ap-southeast-1.amazonaws.com/index.html" -UseBasicParsing
  Invoke-WebRequest -Uri $healthUrl -Headers @{ Origin = $frontendUrl } -UseBasicParsing
  ```
- **Expected result:** All S3 public access block settings are enabled, direct S3 object access returns HTTP 403, and the API response allows the exact CloudFront origin.
- **Actual result:** Passed. All four public access block settings were `true`, direct S3 access returned HTTP 403, and `Access-Control-Allow-Origin` matched the CloudFront frontend URL.
- **Date:** 2026-09-23
- **Artefact path:** `src/infrastructure/frontend.tf` and `src/infrastructure/api.tf`
