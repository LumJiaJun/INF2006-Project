# Repository Audit - 2 October 2026

## Scope

This audit reviewed the tracked repository, local-first workflow, Terraform configuration, security gates, submission metadata, evidence catalogue, branch divergence, and current Terraform state.

## Verified Results

| Check | Result |
|------|--------|
| Tracked repository inventory | 136 files reviewed by automated inventory and targeted inspection |
| Local preflight | Passed with `python tests/local_preflight.py --include-ml` |
| Python unit tests | 37 passed |
| Local HTTP journey | Frontend, health, analytics, model schema, and prediction returned HTTP 200 |
| Python compilation | Passed |
| Frontend JavaScript syntax | Five scripts passed `node --check` |
| Terraform formatting and validation | Passed; validation returned zero errors and zero warnings |
| Terraform state | Zero application resources after the documented 2 October teardown |
| Bandit static analysis | Zero findings using the CI workflow command |
| Python dependency audit | Zero known vulnerabilities in application and analytics requirement sets |
| GitHub workflow syntax | Passed `actionlint` |
| Secret-pattern review | No credential or private-key material found in tracked content |
| GitHub checks | CI, Security Gates, and CodeQL passed on both `main` and `nixon` at the audited revision |

## Architecture and Security Review

- API Gateway keeps health, analytics, and prediction public while history, saved predictions, and chat require a validated Cognito JWT.
- Lambda functions use purpose-specific IAM roles and private subnets across two Availability Zones.
- Security-group egress is scoped to the VPC CIDR and the S3 and DynamoDB prefix lists rather than unrestricted internet egress.
- Private S3 frontend access, CloudFront response headers, WAF controls, encrypted data stores, CloudTrail data events, CloudWatch alarms, and SNS notification paths remain declared in Terraform.
- DynamoDB is an AWS managed regional service rather than a subnet resource; Lambda reaches it through the declared gateway endpoint.
- No material application, infrastructure, or security defect was identified by this local audit.

## Consistency Corrections

- Updated the report and architecture captions to distinguish the Terraform-defined architecture from a currently running stack.
- Recorded that the application was deployed and verified on 1 October, then destroyed on 2 October to stop idle costs.
- Updated the AI-use declaration from 34 to 37 tests and added the verified loopback smoke journey.

## Branch Review

- `main` and `nixon` were synchronized at the start of this audit.
- `brendan` had no commits missing from the audited history.
- `adheesh` retained one older divergent StaySphere/FastAPI commit that conflicts with the selected lightweight serverless architecture; it was not merged wholesale.
- `jj` retained an alternative Azure implementation. It is useful design evidence but is outside the selected AWS deployment and was not merged into the core application.

## Remaining Submission Risks

1. `TEAM_CONTRIBUTIONS.md` still needs truthful role, artefact, test ownership, and reflection entries approved by each member.
2. `video_link.txt` remains a placeholder until the team records and uploads the presentation.
3. The corrected local ZAP DAST run passed, but a new successful GitHub DAST run has not been captured after teardown. Re-deploy before rerunning it if the team wants hosted-workflow evidence.
4. Build the final submission ZIP from a clean committed revision and verify every manifest path from inside that ZIP before submission.

These items are not silently completed because they require team attribution, a presentation URL, or a live deployment.
