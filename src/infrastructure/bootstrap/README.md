# Terraform state bootstrap

This small Terraform root owns the S3 bucket and KMS key used by the main
application backend. State belongs in S3, not Git, KMS, or Secrets Manager.
KMS encrypts the S3 objects; it does not store Terraform state.

For an existing bucket, initialize locally and import it before applying:

```powershell
terraform init -backend=false
terraform import aws_s3_bucket.terraform_state <state-bucket-name>
terraform plan
terraform apply
```

After the first apply, copy both outputs into an ignored `backend.hcl` based on
`backend.hcl.example`, then migrate the bootstrap state into its own S3 key:

```powershell
terraform init -migrate-state -backend-config=backend.hcl
terraform state list
```

Run the same migration from the parent `src/infrastructure` directory using
its own `backend.hcl`. Never migrate an empty local application state over a
non-empty remote state. Review `terraform state list` and `terraform plan`
before every apply.
