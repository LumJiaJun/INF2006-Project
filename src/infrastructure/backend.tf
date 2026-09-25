# Store shared Terraform state outside Git. The bucket is private, encrypted,
# versioned, and scoped to the project AWS account.
terraform {
  backend "s3" {
    bucket       = "airbnb-market-intelligence-tfstate-574816782582"
    key          = "airbnb-market-intelligence/dev/terraform.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true
  }
}
