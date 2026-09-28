# Bounded Load and Overload Safety Test - 2026-09-28

## Purpose

This work validates the load-test harness without performing a DDoS test. Destructive or unbounded traffic is not appropriate for a shared AWS account, and the application stack was intentionally offline during this test.

## Safety Controls Added

- Remote targets must use HTTPS.
- The operator must provide an exact target hostname allowlist.
- The operator must explicitly confirm authorization to test the target.
- JMeter is capped at 50 threads and 120 seconds per invocation.
- The API health test is capped at 100 requests and concurrency 10.
- Loopback targets remain available for safe harness validation.
- JMeter now receives the URL port, fixing local and non-default-port execution.

## Local JMeter Harness Result

A Python static server hosted `src/frontend` on `127.0.0.1:8765`. Apache JMeter 5.6.3 ran the CloudFront browser journey with five threads, a two-second ramp, and an eight-second duration.

```powershell
./tests/run_jmeter.ps1 `
  -FrontendUrl http://127.0.0.1:8765/ `
  -Threads 5 `
  -RampSeconds 2 `
  -DurationSeconds 8 `
  -JMeterCommand "$env:LOCALAPPDATA\Programs\apache-jmeter-5.6.3\bin\jmeter.bat"
```

Observed result:

- Requests: 100
- Throughput: 12.5 requests/second
- Failures: 0
- Average response time: 3.1 ms
- Maximum response time: 97 ms

This result validates the harness and local static-page journey only. It is not AWS performance evidence.

## Authorized AWS Procedure

After an approved deployment, derive the target from Terraform rather than typing an unrelated hostname:

```powershell
$frontendUrl = terraform -chdir=src/infrastructure output -raw frontend_url
$frontendHost = ([Uri]$frontendUrl).Host
./tests/run_jmeter.ps1 `
  -FrontendUrl $frontendUrl `
  -Threads 10 `
  -RampSeconds 10 `
  -DurationSeconds 30 `
  -AllowedHost $frontendHost `
  -IConfirmAuthorizedTarget `
  -JMeterCommand "$env:LOCALAPPDATA\Programs\apache-jmeter-5.6.3\bin\jmeter.bat"

$healthUrl = terraform -chdir=src/infrastructure output -raw health_url
$apiHost = ([Uri]$healthUrl).Host
python tests/load_health.py `
  --url $healthUrl `
  --requests 20 `
  --concurrency 2 `
  --allowed-host $apiHost `
  --confirm-authorized-target
```

The API check accepts HTTP 200 and controlled HTTP 429 responses. Any 5xx response fails the test. CloudWatch API 5xx, latency, Lambda errors, and throttles must be reviewed alongside client results.

The higher-concurrency 2026-09-23 result remains documented in `evidence/test-resilience.md`: the account-wide Lambda concurrency quota caused HTTP 503 responses. It must not be repeated or described as DDoS protection evidence until the quota and test authorization are reviewed.
