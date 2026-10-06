# Chatbot Accuracy and Grounding Review - 2026-10-04, Updated 2026-10-06

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
- Added explicit boundaries for causal claims, invalid night counts, fees,
  taxes, live availability, booking, host contact, payments, and actual Airbnb
  listing links.
- Clarified that public estimation and Markets analytics do not require sign-in;
  Cognito email verification and required TOTP MFA protect saving predictions,
  private history, and chat.
- Added deterministic post-generation rewrites for promotional phrases such as
  `gross nightly income`, `estimated revenue`, and `revenue potential`.
- Changed the deployed evaluator so every scenario receives its exact disposable
  DynamoDB fixture under a unique synthetic identity, followed by cleanup in
  `finally`.

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

- The local preflight passed 47 unit tests, Python compilation, five JavaScript
  syntax checks, Terraform formatting and validation, synthetic model training,
  and loopback frontend/API checks.
- The final local Bedrock evaluation passed 24 of 24 scenarios.
- The final deployed Lambda evaluation passed the same 24 of 24 scenarios.
- Scenarios covered exact newest-record recall and dates, three-night arithmetic,
  invalid night counts, empty and unmatched history, same-currency and mixed-
  currency comparisons, supported currencies, dataset scope, held-out metrics,
  public/private authentication boundaries, investment refusal, prompt
  injection, out-of-scope refusal, architecture, model responsibility,
  diagnostic-not-causal language, unsupported cities, unavailable live
  analytics, unknown deployment status, private account data, fees, live
  availability, booking, host contact, and transaction boundaries.
- A separate deployed two-identity check confirmed that the owner retrieved one
  saved record while another synthetic identity retrieved zero. This proves the
  handler and DynamoDB partition behavior but is not presented as a two-browser
  Cognito journey.
- The separate integration script confirmed that the deployed Lambda retrieved
  Paris, EUR 123.45, and 17 amenities from one isolated DynamoDB record.
- The deployed evaluator deleted every per-scenario and isolation record in
  `finally`.
- An unauthenticated `POST /chat` request returned HTTP `401`.
- Thirty-six recent chat log events contained none of the tested prompt, user,
  price, or neighbourhood markers. All five alarms reported `OK`.
- The real dataset Glue run succeeded, the deployed smoke test returned ten city
  summaries and a EUR 65.98 prediction, and the final Terraform plan had no
  changes.

## Exploratory failures and corrections

Pre-final runs were retained under ignored `tmp/` during development. They
exposed both evaluator phrase brittleness and real response risks. The evaluator
was broadened only for semantically equivalent safe wording such as `not
currently supported` and `direct comparison is not meaningful`. The prompt and
output guard were changed for substantive issues: an answer implied MFA was
needed for the public estimator, one invented `near-superhost`, one suggested an
actual listing link, and one offered `gross nightly income`. The final raw local
and deployed JSON artefacts both report 24 passes and zero failures.

## Interpretation and limits

The evaluation uses explicit expected facts and forbidden claims. It provides
repeatable evidence for representative questions but cannot prove correctness
for every prompt or future model behavior. Temperature zero improves
repeatability but does not make a managed generative model formally
deterministic. Exact live Athena values are not copied into assistant context;
the assistant directs users to the Markets page when a requested value is not
available. The assistant remains authenticated to protect private history and
control Bedrock cost.

- **Artefact paths:** `tests/evaluate_chatbot.py`,
  `tests/evaluate_deployed_chatbot.py`, `tests/test_chat.py`,
  `evidence/chatbot-evaluation-local-2026-10-06.json`, and
  `evidence/chatbot-evaluation-deployed-2026-10-06.json`.
