# Live Fixes and Recheck - 2026-10-07

Region ap-southeast-1. Redacted: no account IDs, tokens, or personal data.

## Defects found and fixed

| Defect | Cause | Fix | Check |
|--------|-------|-----|-------|
| Signed-in estimator showed "Failed to fetch" | The frontend sends an `Idempotency-Key` header on `POST /predictions`, but API Gateway CORS allowed only `authorization` and `content-type`, so the browser preflight failed. Signed-out `POST /predict` does not send the header and was unaffected. | Added `idempotency-key` to `allow_headers` in `src/infrastructure/api.tf` and applied a reviewed single-resource plan. | Before: preflight with `Access-Control-Request-Headers: content-type,authorization,idempotency-key` returned 204 with no CORS headers. After: it returned `access-control-allow-headers: authorization,content-type,idempotency-key`. A signed-in browser estimate was later confirmed manually; see `manual-browser-verification-2026-10-07.md`. |
| Chatbot could not answer market questions | The chat Lambda received no per-city values and was told to redirect users to the Markets page. | Packaged `src/backend/chat/market_stats.json` (a snapshot of the live `/analytics` response plus precomputed rankings) and instructed the model to quote it, to use the rankings for highest/lowest questions, and never to infer demand from listing counts. `maxTokens` raised from 220 to 300. | See evaluation below. |
| Chatbot named the wrong city for "most listings" | First grounded version relied on the model scanning ten rows (New York answered, Paris correct at 64,020). | Added `market_stats.rankings`. | Redeployed answer: Paris, 64,020, described as supply not demand. |

The 220-token figure in earlier evidence documents describes the state on the
dates they were written; the deployed cap is now 300 tokens.

## Chatbot evaluation

`python tests/evaluate_deployed_chatbot.py` (isolated synthetic users, direct Lambda invocation,
anonymous API probe) passed 26 of 26 scenarios on two consecutive runs. The
suite now has 26 scenarios: the three failing expectations from the first run
were corrected (two were over-strict phrase checks; one asserted the old
no-market-data behaviour) and three grounding scenarios were added
(`grounded_market_median`, `grounded_market_ranking`, `listing_count_not_demand`).
Raw results: `chatbot-evaluation-deployed-2026-10-07.json`. These are
single-sample model outputs at temperature 0, not a statistical guarantee. A
real Cognito browser session with MFA was not driven.

`market_stats.json` was compared with the live `/analytics` response and matched.
It is a snapshot; regenerate it if the analytics data changes.

## Repository and infrastructure checks

- `python -m pytest tests`: 47 passed.
- `python tests/local_preflight.py --include-ml`: completed successfully, also from a clean `git archive` copy.
- `terraform fmt -check -recursive`: clean. `terraform validate`: valid.
- `terraform plan` with the live prediction image tag and alert email: only the chat package hash differed (line-ending artefact); a reviewed saved plan was applied and the next plan reported no changes.
- Without `-var="alert_email=..."` a plan proposes destroying the SNS email subscription, and the default `prediction_image_tag` differs from the deployed tag. Always pass the live values when planning against this stack.

## Live smoke, load, and security probes

- `tests/smoke_api.ps1`: frontend security headers, prediction (EUR 65.98), analytics (10 cities), protected-route rejection, and malformed-input validation all passed.
- `tests/load_health.py`: 60 requests at concurrency 4 to `/health` returned 38 x 200 and 22 x 429, median 229 ms, max 1364 ms. The 429s are the intended API Gateway route throttle (`throttling_rate_limit` 1-2 requests per second), not an outage.
- Unauthenticated `GET /history`, `POST /predictions`, and `POST /chat` returned 401; a malformed bearer token returned 401.
- Malformed JSON to `/predict` returned 400; an injection-style city string returned 400 validation error; unknown route returned 404.
- A preflight from `https://evil.example` received no `access-control-allow-origin` header.
- Frontend response carried HSTS, CSP, and X-Frame-Options DENY.
- Throttle responses are `{"message":"Too Many Requests"}` with no internal detail.

## Not verified

- A second-account isolation journey, fresh sign-up with TOTP MFA, and phone-width layout (see `manual-browser-verification-2026-10-07.md` for what was verified).
- Delivery of a new alarm email to the (confirmed) SNS subscription was not retested.
