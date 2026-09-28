# Frontend Refinement and Bounded Load Evidence - 2026-09-28

## Deployment

Terraform updated the three static frontend objects (`index.html`, `app.js`, and `styles.css`) in the private S3 origin. A CloudFront `/*` invalidation completed before the live checks began.

The estimator now exposes its market, listing, and host stages and updates a visual readiness indicator as the user supplies inputs. The implementation only changes fixed CSS classes and text content; it does not render user input as HTML.

## Live Regression

`tests/smoke_api.ps1` passed against the Terraform-derived CloudFront and API URLs:

- The frontend assets and security headers were present.
- `GET /health` returned healthy.
- `POST /predict` returned a Paris estimate of `EUR 65.98`.
- `GET /analytics` returned ten city summaries.
- Protected routes rejected unauthenticated requests.
- A malformed prediction request was rejected safely.

## Bounded JMeter Results

The CloudFront journey used five threads, a five-second ramp, and a 15-second duration:

- 65 requests
- 0 failures
- 669.6 ms average response time
- 1,391 ms maximum response time

The new Lambda-backed health profile used one paced visitor for 20 seconds. Its 700 ms timer keeps the request rate at about 1.4 requests per second, below the configured API Gateway limit of two requests per second:

- 26 requests
- 0 failures
- 48.7 ms average response time
- 352 ms maximum response time

The JMeter wrappers require HTTPS, an exact hostname allowlist, and an explicit authorization switch. HTML reports are kept under ignored `tmp/` directories. These controlled checks show expected behaviour at the selected load, not unlimited Lambda capacity or DDoS resistance.

## Operational Check

After both JMeter runs, the API server-error, health-throttle, health, prediction, analytics, and chat alarms were all `OK`.

## Remaining Capacity Work

The health route is intentionally rate-limited, and model inference remains validated functionally rather than under concurrency. Before claiming a model-throughput target, agree on an SLO and cost budget, request any needed AWS concurrency increase, then perform a separate authorised prediction-route test with CloudWatch p95 latency, errors, throttles, and spend reviewed.
