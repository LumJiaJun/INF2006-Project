# Backend values are supplied from an ignored backend.hcl file so account-specific
# identifiers never enter Git. See backend.hcl.example and bootstrap/README.md.
terraform {
  backend "s3" {}
}
