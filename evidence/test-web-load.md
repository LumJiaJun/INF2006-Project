# JMeter Web Load Test

**Test date:** 2026-09-24

**Tool:** Apache JMeter 5.6.3, verified against the official SHA-512 checksum

**Target:** Deployed CloudFront frontend in the project AWS account

## Method

The non-GUI plan `tests/jmeter/web-load.jmx` simulated 25 visitors, ramped over 15 seconds, for a 45-second scheduled duration. Each loop requested the home page, stylesheet, estimator JavaScript, city market page and project page with a 350 ms reading pause. The run used browser caching rules but cleared the cache for each new journey.

```powershell
./tests/run_jmeter.ps1 `
  -FrontendUrl (terraform -chdir=src/infrastructure output -raw frontend_url) `
  -Threads 25 `
  -RampSeconds 15 `
  -DurationSeconds 45 `
  -JMeterCommand "$env:LOCALAPPDATA\Programs\apache-jmeter-5.6.3\bin\jmeter.bat"
```

## Result

- Total requests: 929
- Throughput: 20.3 requests/second
- Failures: 0 (0.00%)
- Mean response time: 666.9 ms
- Minimum response time: 362 ms
- Maximum response time: 1,508 ms

The bounded profile passed. It demonstrates successful CloudFront static delivery at this test level, not an unlimited scaling claim or a measured breaking point. Generated JTL and HTML report files remain under ignored `tmp/` storage because they contain run-specific output.
