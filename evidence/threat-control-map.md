# Threat-Control Map

Map named threats to the controls that mitigate them, with evidence links.

| Threat | Control implemented | Evidence |
|--------|---------------------|----------|
| Direct public access to frontend objects | S3 Block Public Access and a bucket policy scoped to the CloudFront distribution | `src/infrastructure/frontend.tf`, `evidence/test-security.md` |
| Over-privileged compute identity | The health Lambda role can only write to its dedicated CloudWatch log group | `src/infrastructure/api.tf` |
| Unapproved browser origins calling the API | API Gateway CORS allows only the deployed CloudFront origin | `src/infrastructure/api.tf`, `evidence/test-security.md` |
| Unencrypted browser traffic | CloudFront and API Gateway expose HTTPS endpoints and CloudFront redirects HTTP requests to HTTPS | `src/infrastructure/frontend.tf` |
| Secret leakage through source control | Local environment files, Terraform state, private keys, and sensitive variable files are ignored | `.gitignore`, `src/.env.example` |

## Secrets handling

No application secret is required by the current milestone. Terraform uses the standard AWS credential chain outside the repository, and Lambda uses an IAM execution role. No AWS access key, token, password, or private key is committed. Future secrets must use an appropriate managed service or runtime reference and must not be stored in Git.
