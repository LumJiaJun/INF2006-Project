# Manual Browser Verification - 2026-10-07

Performed by Nixon Lee Disheng in a desktop browser against the live CloudFront
site after the API CORS fix. Redacted: no tokens, account IDs, or URLs recorded.
Observations come from the operator's reported page content, not from automated
tooling.

## Observed

| Check | Result |
|-------|--------|
| Signed-out estimator, default Bangkok profile | Returned THB 714.56 (34% below the historical Bangkok median) with the model-estimate disclaimer. The "+5 amenities" what-if returned THB 724.41. |
| Signed-in estimator (the path previously failing with "Failed to fetch") | Same profile returned THB 714.56 and the page stated the estimate was saved to the user's history. No fetch error. |
| Signed-in history | "Refresh history" listed 1 most recent prediction: Bangkok, Bang Bon, entire place for 2 guests, THB 714.56, timestamped 07/10/2026 22:27:05 local time. |
| Signed-in chat before saving | Asked "What is my latest saved prediction?"; the guide said there were none and explained how to create one. |
| Signed-in chat after saving | Same question returned the saved estimate: Bangkok, Bang Bon, entire place, 1 bedroom, 2 guests, 8 amenities, minimum 2 nights, estimate 714.56 THB, model version 1.0.0, 14:27 UTC. The widget reported using 1 saved prediction. |
| Signed-in chat market question | "give me estimated paris median" returned EUR 80.18 with context, matching the Markets page. |
| Two-account isolation | Operator reported: with a second, different account signed in from a separate browser session, "Recent predictions" was empty after refresh and did not show the first account's saved Bangkok estimate. No screenshot retained; this is an operator observation. |
| Local comparison panel | Added the estimate to the browser-local comparison (1 of 3 scenarios). |

## Interpretation

The 7 October CORS fix (`idempotency-key` added to the API allow-list) restored
signed-in estimation end to end, and the saved record is readable by the
history view and by the chat Lambda for the same user.

## Not verified here

- Fresh sign-up with email verification and TOTP MFA setup.
- Phone-width layout.
- Alarm email delivery to the confirmed SNS subscription.
