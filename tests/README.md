# tests/

Automated tests, API collection or repeatable test scripts.

At least four tests are required (see report Section 6 and evidence/):
1. Functional workflow test
2. Security control test
3. Data / AI validation test
4. Scalability, resilience or recovery test

## How to run

Run the complete offline submission preflight from the repository root:

```bash
pip install -r tests/requirements.txt
python tests/local_preflight.py --include-ml
```

This runs unit tests, Python compilation, manifest path validation, available
frontend and Terraform checks, and an end-to-end model training smoke test on
committed synthetic data. It does not require AWS credentials or a live stack.

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
python tests/load_health.py `
  --url <health-url> `
  --requests 20 `
  --concurrency 2 `
  --allowed-host <api-hostname> `
  --confirm-authorized-target
```

The command passes only when every response is HTTP 200 or an explicit HTTP 429 throttle response and at least one request succeeds.

Run the CloudFront browser journey with Apache JMeter 5.6.3 or newer:

```powershell
./tests/run_jmeter.ps1 `
  -FrontendUrl <frontend-url> `
  -Threads 10 `
  -RampSeconds 10 `
  -DurationSeconds 30 `
  -AllowedHost <cloudfront-hostname> `
  -IConfirmAuthorizedTarget
```

The plan repeatedly loads the home page, shared assets, market guide, and project page. The wrappers reject non-HTTPS remote targets, require an exact hostname allowlist and authorization confirmation, and cap concurrency and duration. These are load and overload-rejection checks, not DDoS tests. Generated JTL and HTML reports are stored under ignored `tmp/` paths.

Run the paced Lambda-backed health profile with JMeter:

```powershell
$healthUrl = terraform -chdir=src/infrastructure output -raw health_url
$apiHost = ([Uri]$healthUrl).Host
./tests/run_jmeter_health.ps1 `
  -HealthUrl $healthUrl `
  -AllowedHost $apiHost `
  -IConfirmAuthorizedTarget
```

This profile uses one paced visitor at about 1.4 requests per second, below the deployed two-request-per-second API Gateway limit. It asserts HTTP 200 and the expected health JSON, so any Lambda, API Gateway, or response failure fails the run.

Run the controlled deployed chat integration check only against an AWS environment you own:

```powershell
$table = terraform -chdir=src/infrastructure output -raw prediction_history_table_name
$chatFunction = terraform -chdir=src/infrastructure output -raw chat_lambda_name
./tests/run_chat_integration.ps1 `
  -TableName $table `
  -ChatFunctionName $chatFunction `
  -IConfirmAuthorizedTarget
```

The script creates one synthetic prediction under a random test user, directly invokes the deployed chat Lambda with that user claim, confirms the safe `history_record_count: 1` completion telemetry and bounded Bedrock reply, then deletes the test record in `finally`. It does not replace the separate browser test of Cognito and API Gateway JWT enforcement.
