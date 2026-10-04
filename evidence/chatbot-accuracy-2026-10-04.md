# Chatbot Accuracy and Grounding Review - 2026-10-04

## Scope

This review evaluated the bounded Claude Haiku assistant, its server-controlled
platform facts, and retrieval of the authenticated user's ten newest DynamoDB
prediction records. Cognito remained enabled throughout. The public API route
continued to require a valid JWT; direct Lambda invocation was used only as an
operator integration test with synthetic claims and disposable records.

## Improvements

- Added verified platform facts for supported cities and currencies, dataset
  scope, model method and metrics, analytics capabilities, required TOTP MFA,
  architecture, and AI/model responsibility boundaries.
- Structured history as newest-first records plus record count, currencies
  present, and whether direct price comparison is allowed.
- Set model temperature to zero, retained the 220-token generation cap and
  120-word response boundary, and removed unsupported Markdown before returning
  plain text to the browser.
- Required exact use of saved prices, dates, currencies, and listing fields;
  prohibited invented history, unsupported forecasts, cross-currency ranking,
  account-setting claims, and confusion between Bedrock and the scikit-learn
  pricing model.

## Tests performed

Commands were run from the repository root with authorized AWS credentials:

```powershell
python tests/local_preflight.py --include-ml
python tests/evaluate_chatbot.py --i-confirm-authorized-account
python tests/evaluate_deployed_chatbot.py `
  --function-name <terraform-chat-output> `
  --table-name <terraform-history-output> `
  --chat-url <terraform-chat-url> `
  --i-confirm-authorized-target
```

- The local preflight passed 41 unit tests, Python compilation, five JavaScript
  syntax checks, Terraform formatting and validation, synthetic model training,
  and loopback frontend/API checks.
- The local Bedrock evaluation passed 16 of 16 scenarios.
- The deployed Lambda evaluation passed the same 16 of 16 scenarios.
- Scenarios covered exact newest-record recall, three-night arithmetic, empty
  history, mixed currencies, supported currencies, dataset scope, held-out
  metrics, required MFA, investment refusal, prompt injection, out-of-scope
  refusal, architecture, unsupported cities, unavailable live analytics,
  unknown deployment status, and private account data.
- The separate integration script confirmed that the deployed Lambda retrieved
  Paris, EUR 123.45, and 17 amenities from one isolated DynamoDB record.
- The deployed evaluator deleted both disposable records. A follow-up scan found
  zero test records with the integration prefixes.
- An unauthenticated `POST /chat` request returned HTTP `401`.
- Thirty-six recent chat log events contained none of the tested prompt, user,
  price, or neighbourhood markers. All five alarms reported `OK`.
- The real dataset Glue run succeeded, the deployed smoke test returned ten city
  summaries and a EUR 65.98 prediction, and the final Terraform plan had no
  changes.

## Interpretation and limits

The evaluation uses explicit expected facts and forbidden claims. It provides
repeatable evidence for representative questions but cannot prove correctness
for every prompt or future model behavior. Temperature zero improves
repeatability but does not make a managed generative model formally
deterministic. Exact live Athena values are not copied into assistant context;
the assistant directs users to the Markets page when a requested value is not
available. The assistant remains authenticated to protect private history and
control Bedrock cost.
