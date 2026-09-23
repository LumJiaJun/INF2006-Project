# AI Use Declaration

Declare all AI tools and external baselines used, where they were used, the
verification the team performed, and any licences/attribution.

## Tools used

| Tool | Where it was used | Purpose |
|------|-------------------|---------|
| OpenAI Codex | `AGENTS.md`, `.gitignore`, `README.md`, `src/`, `tests/`, `evidence/`, and `project_manifest.yaml` | Repository inspection, implementation support, Terraform configuration, tests, documentation, and deployment verification. |

## Sources and baselines

| Source / baseline | URL | Licence | Modifications made by the team |
|-------------------|-----|---------|--------------------------------|
| <name> | <url> | <licence> | <substantive changes> |

## Verification performed

- Reviewed the Terraform plan before each apply and confirmed that it contained no destructive actions.
- Ran `terraform fmt -check`, `terraform validate`, Python unit tests, and JavaScript syntax checking.
- Verified the deployed CloudFront frontend, API health response, CORS restriction, direct S3 denial, and CloudWatch log event.
- The team remains responsible for reviewing future generated work and validating all final claims.

## Licences and attribution

- <Any third-party code/assets and their licences.>
