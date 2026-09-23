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
