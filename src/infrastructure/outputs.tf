# Outputs expose deployment identifiers needed for testing and operations.
output "frontend_bucket_name" {
  description = "Private S3 bucket containing the static frontend."
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution identifier."
  value       = aws_cloudfront_distribution.frontend.id
}

output "frontend_url" {
  description = "Public HTTPS URL for the static frontend."
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "health_url" {
  description = "Public API health endpoint."
  value       = "${aws_apigatewayv2_api.platform.api_endpoint}/health"
}

output "prediction_ecr_repository_url" {
  description = "ECR repository URL for the prediction Lambda image."
  value       = aws_ecr_repository.prediction.repository_url
}

output "prediction_url" {
  description = "Public model prediction endpoint."
  value       = "${aws_apigatewayv2_api.platform.api_endpoint}/predict"
}

output "authenticated_prediction_url" {
  description = "Cognito-protected model prediction endpoint that saves history."
  value       = "${aws_apigatewayv2_api.platform.api_endpoint}/predictions"
}

output "prediction_history_url" {
  description = "Cognito-protected prediction history endpoint."
  value       = "${aws_apigatewayv2_api.platform.api_endpoint}/history"
}

output "cognito_user_pool_id" {
  description = "Cognito user pool identifier."
  value       = aws_cognito_user_pool.users.id
}

output "cognito_user_pool_client_id" {
  description = "Public Cognito application client identifier."
  value       = aws_cognito_user_pool_client.frontend.id
}

output "cognito_hosted_ui_url" {
  description = "Cognito hosted UI base URL."
  value       = "https://${aws_cognito_user_pool_domain.users.domain}.auth.${var.aws_region}.amazoncognito.com"
}

output "prediction_history_table_name" {
  description = "DynamoDB table used for user prediction history."
  value       = aws_dynamodb_table.prediction_history.name
}

output "data_lake_bucket_name" {
  description = "Private S3 bucket containing raw, processed, model, and query-output data."
  value       = aws_s3_bucket.data_lake.id
}

output "glue_transform_job_name" {
  description = "Glue job that converts raw listings CSV data to partitioned Parquet."
  value       = aws_glue_job.listings_transform.name
}

output "analytics_url" {
  description = "Public market analytics endpoint backed by Athena."
  value       = "${aws_apigatewayv2_api.platform.api_endpoint}/analytics"
}

output "operational_alerts_topic_arn" {
  description = "Encrypted SNS topic used by CloudWatch operational alarms."
  value       = aws_sns_topic.operational_alerts.arn
}

output "operations_dashboard_name" {
  description = "CloudWatch dashboard containing API and Lambda operational metrics."
  value       = aws_cloudwatch_dashboard.operations.dashboard_name
}
