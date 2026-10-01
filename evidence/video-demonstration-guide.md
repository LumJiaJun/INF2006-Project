# Functional Proof Video Guide

Target duration: 5-8 minutes. Record one continuous, consented demonstration where practical. Do not expose account IDs, email addresses, passwords, MFA seeds or codes, access tokens, Cognito subjects, private URLs, Terraform state, or personal prediction data.

## Recording sequence

1. State the problem: existing and prospective hosts need price-estimation scenarios and historical market context before listing or evaluating a property for hosting.
2. Open the live CloudFront website and show the security indicator and guided estimator.
3. Build one potential listing, generate a real estimate, and explain its local currency, model version, market comparison, and disclaimer.
4. Change capacity, bedrooms, room type, or amenities; generate another estimate; add both to the browser-local comparison workspace; explain the difference and currency safeguard.
5. Open the public market explorer and explain listing count, median price, rating, data snapshot limitations, and why local currencies are not globally compared.
6. Sign in through Cognito using a consented demonstration account. Hide the email address and every verification or MFA code during editing.
7. Save an authenticated estimate and show that only that account's history appears.
8. Ask the AI assistant to compare recent estimates, then try one adversarial request such as asking it to reveal its system prompt or another user's records. Show the bounded response without exposing the actual prompt or tokens.
9. Open the health endpoint, CloudWatch dashboard, five alarms, recent redacted Lambda log events, and the deployed Lambda functions.
10. Show DynamoDB encryption and point-in-time recovery status without opening personal records.
11. Show S3 Block Public Access and encryption for the frontend and data-lake buckets, the ECR image scan result, and the two-AZ private Lambda VPC with endpoints.
12. Run `terraform output` with sensitive identifiers obscured and show successful GitHub CI, security, and CodeQL workflows.
13. Finish with limitations: snapshot data, material model error, no occupancy or return forecast, no property-purchase advice, local currencies, and no tested regional failover.

## Evidence handling

- Pause recording or blur the screen before authentication codes or personal details appear.
- Use resource names only where they do not expose an account ID or personal address.
- Do not open Terraform state, browser developer storage, authorization headers, network tokens, or raw DynamoDB user records.
- Add the final public or institution-accessible presentation URL to `video_link.txt`; the video supplements but does not replace repository evidence.
