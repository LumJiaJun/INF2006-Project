# Local Development Verification - 2026-10-02

## Objective

Verify that the core public user journey can run before AWS deployment rather
than treating the cloud environment as the first testing location.

## Command

```text
python tests/local_preflight.py --include-ml
```

## Observed result

The preflight trained the deterministic sample model, started the application
on an ephemeral `127.0.0.1` port, and made real HTTP requests to:

- `/` for the production frontend HTML;
- `/api/health` for the local health response;
- `/api/analytics` for ten synthetic city summaries;
- `/model-options.json` for the model-derived local form schema; and
- `/api/predict` for a positive model-backed nightly-price estimate.

All requests returned HTTP 200. The complete preflight also retained 37 passing
unit tests, Python and JavaScript syntax checks, manifest path validation, and
Terraform formatting and validation.

## Scope boundary

The local server binds to loopback by default, uses committed synthetic data,
and does not require AWS credentials. It validates application behavior, not
AWS managed-service configuration. Cognito, JWT enforcement, private DynamoDB
history, Bedrock, Glue/Athena execution, CloudFront/WAF, VPC endpoints, alarms,
SNS delivery, resilience, and scaling continue to require the separately
recorded cloud tests.
