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
