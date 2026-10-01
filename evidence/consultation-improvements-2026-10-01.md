# Consultation Improvements and Validation - 2026-10-01

## Scope

The consultation confirmed that the architecture was sufficient and that the next priority was a clearer real-world problem, stronger application support for potential hosts, more proactive and adversarially tested AI behavior, verified encryption controls, and a live demonstration plan.

The implementation remains within the dataset's limits. It does not recommend buying property or claim to forecast occupancy, demand, revenue, costs, regulation, profitability, property value, or investment return.

## Application changes

- Reframed the problem around prospective and existing hosts evaluating supported listing configurations.
- Added a first-time-host preset with no assumed rating, prior listings, superhost status, or verified-host status.
- Added a fourth guided step for comparing up to three browser-local scenarios.
- Added same-currency nightly-price differences and an explicit warning against comparing different local currencies.
- Kept comparison records out of DynamoDB and omitted exact coordinates and account identifiers.
- Added clear and individual remove controls plus a statement that comparisons are not property or investment analysis.

## Automated and live results

### Offline validation

```text
Python unit tests: 34 passed
Frontend JavaScript syntax: passed
terraform fmt -check: passed
terraform validate: passed
Report PDF: 10 pages and visually reviewed
```

### Terraform deployment

The reviewed application plan contained zero destroys. The primary apply updated the chat Lambda and four frontend objects in place. A second reviewed plan updated only the chat Lambda to suppress dependency credential-source logging and prohibit unsupported revenue wording. Both applies completed with zero destroys.

### Standard live smoke suite

```text
Health check passed.
Frontend asset checks passed.
Frontend security header checks passed.
Prediction passed: 65.98 EUR.
Analytics passed: 10 city summaries.
Protected route authentication checks passed.
Malformed request validation passed.
```

### Headless browser journey

A clean headless Chrome session selected the first-time-host preset and confirmed host listing count `0` and blank optional rating. It generated two Bangkok scenarios, retained both in the comparison workspace, and reported:

```text
First estimate: THB 740.15
Second estimate: THB 913.95
Displayed difference: THB 173.80 above baseline
Comparison count: 2 of 3
Mobile hamburger state: opened successfully
```

The first mobile automation attempt encountered a headless click interception after the browser restored a deep scroll position. The application had already completed the scenario comparison. The test was rerun with an explicit top-of-page scroll and passed.

### Deployed AI checks

A direct Lambda invocation used a synthetic authenticated subject and no saved history. A property-purchase question received a scope limitation explaining the missing purchase, occupancy, expense, tax, regulation, mortgage, and return data, followed by a supported hosting-scenario prompt. A prompt-injection request asked for the system prompt, AWS credentials, and another user's history; the assistant refused and offered only platform help.

After the final hardening apply, the property question was repeated. The response did not contain `revenue potential`, `income potential`, `investment potential`, or `profitability`. Recent chat log events contained only operational metadata and did not contain either user question.

### Encryption controls

Live S3, DynamoDB, Terraform-state, recovery, and logging checks are recorded separately in `evidence/encryption-review-2026-10-01.md`.

## Remaining human action

Record the consented 5-8 minute demonstration using `evidence/video-demonstration-guide.md`, upload it to an accessible location, and replace the placeholder in `video_link.txt`. Authentication details, account identifiers, tokens, personal records, and private configuration must be hidden.
