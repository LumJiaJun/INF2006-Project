# Full Repository Audit - 2026-10-01

## Scope

The audit covered all 125 tracked files, Git history and branch state, backend handlers, frontend trust boundaries, Terraform, IAM, CI/CD, dependency controls, documentation, evidence paths, the report PDF, and the deployed development environment. It did not perform destructive recovery or unbounded load testing.

## Automated validation

- All 34 Python unit tests passed.
- Every frontend JavaScript file passed `node --check`.
- Backend, analytics, and test Python sources compiled successfully.
- Both Terraform roots passed formatting and validation.
- Tracked YAML, JSON, JMeter XML, PowerShell scripts, manifest paths, and Markdown relative links were valid.
- `report.pdf` contained ten pages with no replacement glyphs.
- No tracked Terraform state, plan, environment file, Python cache, credential pattern, or file larger than 5 MB was found.
- GitHub CI, Security Gates, dependency audits, Bandit, and CodeQL passed for the reviewed merge revision.

## Application and security review

- API Gateway JWT authorization protects saved predictions, history, and chat.
- History ownership is derived from the verified Cognito subject claim.
- Prediction inputs are allowlisted and bounded; analytics executes a fixed query rather than user SQL.
- Browser-rendered API and model values use text nodes. The single `innerHTML` assignment is a static SVG launcher with no untrusted input.
- OAuth uses authorization code with PKCE and state validation. Active ID tokens remain in session storage, so script compromise remains a documented residual risk.
- Lambda roles are purpose-specific. The wildcard EC2 resource is limited to network-interface actions that do not support resource-level permissions; the KMS administration wildcard is confined to the account-root key policy.
- The CloudFront origin and data lake are private, encrypted, versioned, TLS-only, and public-access blocked. WAF, security headers, CloudTrail, API throttling, bounded AI output, and encrypted SNS alerts are deployed.

## Live verification

- All five Lambda functions were `Active`, reported successful updates, and used two private subnets and one Lambda security group.
- S3 and DynamoDB gateway endpoints plus Logs, Athena, and Bedrock Runtime interface endpoints were available.
- Prediction history and idempotency tables reported KMS server-side encryption; history continuous backups and point-in-time recovery were enabled.
- All five project alarms were `OK`, CloudTrail was logging without a delivery error, the SNS email subscription was confirmed, and the Lambda concurrency quota was 1,000.
- The live smoke suite passed frontend assets, security headers, health, prediction, ten-city analytics, anonymous protected-route rejection, and malformed-request validation.

## Corrected findings

1. The Terraform prediction-image default and image-build guide still referenced `1.0.3` while the deployed immutable image was `1.0.4`; both now reference `1.0.4`.
2. The deployment workflow did not pass the Terraform alert-email variable and could have planned removal of the confirmed SNS subscription. The protected GitHub `ALERT_EMAIL` variable is now required for deployment planning.
3. Git line-ending normalization caused three source hashes to differ from the deployed objects after commit. A reviewed in-place apply resynchronised the chat Lambda and two frontend objects with zero destruction.
4. The primary architecture diagram incorrectly drew a Bedrock flow from the data lake. It now draws the protected chat Lambda to Bedrock flow.

## Remaining limitations

- `video_link.txt` remains a presentation placeholder; the brief does not allow a video to replace repository evidence.
- `TEAM_CONTRIBUTIONS.md` intentionally contains only names and Nixon's agreed role. Each member must add factual artefacts, tests, and reflection before submission.
- Multi-user browser isolation, live authenticated idempotent retry, restore cutover, cross-region recovery, and a corrected GitHub-hosted DAST rerun remain unclaimed.
- Lambda `Errors` alarms detect unhandled runtime failures; handled application failures return 5xx and are covered by the API Gateway 5xx alarm.
- The public development API deliberately permits anonymous estimates and analytics. CORS is a browser control, not API authentication; throttling bounds casual abuse but is not DDoS certification.
- The VPC and two-AZ endpoints improve private service access but add fixed cost and do not make regional managed services multi-region.
