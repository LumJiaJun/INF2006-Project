output "state_bucket_name" {
  description = "Bucket to place in the application backend.hcl file."
  value       = aws_s3_bucket.terraform_state.id
}

output "state_kms_key_arn" {
  description = "KMS key ARN to place in the application backend.hcl file."
  value       = aws_kms_key.terraform_state.arn
}
