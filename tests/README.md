# tests/

Automated tests, API collection or repeatable test scripts.

At least four tests are required (see report Section 6 and evidence/):
1. Functional workflow test
2. Security control test
3. Data / AI validation test
4. Scalability, resilience or recovery test

## How to run

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Run the deployed API smoke test from the repository root:

```powershell
$frontendUrl = terraform -chdir=src/infrastructure output -raw frontend_url
$apiBaseUrl = (terraform -chdir=src/infrastructure output -raw health_url) -replace '/health$', ''
./tests/smoke_api.ps1 -FrontendUrl $frontendUrl -ApiBaseUrl $apiBaseUrl
```

Run the bounded live health check only against an environment you own:

```powershell
python tests/load_health.py --url <health-url> --requests 20 --concurrency 2
```

The command passes only when every response is HTTP 200 or an explicit HTTP 429 throttle response and at least one request succeeds.

Run the CloudFront browser journey with Apache JMeter 5.6.3 or newer:

```powershell
./tests/run_jmeter.ps1 `
  -FrontendUrl <frontend-url> `
  -Threads 10 `
  -RampSeconds 10 `
  -DurationSeconds 30
```

The plan repeatedly loads the home page, shared assets, market guide, and project page. Start with the bounded defaults and increase concurrency only after reviewing account quotas and prior results. Generated JTL and HTML reports are stored under ignored `tmp/` paths.
