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

## Prediction input validation and least privilege

- **Objective:** Verify that malformed or unsupported prediction requests are rejected without exposing stack traces and that the prediction role cannot access unrelated AWS data services.
- **Setup:** Public `POST /predict` route, prediction handler validation, and a dedicated Lambda execution role.
- **Command / steps:** Run `python -m unittest discover -s tests -p "test_prediction.py" -v`, run `tests/smoke_api.ps1`, and inspect `aws_iam_role_policy.prediction_lambda_logs` in `src/infrastructure/prediction.tf`.
- **Expected result:** Invalid JSON, missing fields, unsupported categories, invalid coordinates, and unreasonable values return HTTP 400. The client receives safe errors. The Lambda role can write only to its own log group.
- **Actual result:** Passed. Six focused prediction-handler tests passed, the live malformed request returned HTTP 400, and the role policy contains only `logs:CreateLogStream` and `logs:PutLogEvents` on the prediction log group.
- **Date:** 2026-09-23
- **Artefact path:** `tests/test_prediction.py`, `tests/smoke_api.ps1`, and `src/infrastructure/prediction.tf`
