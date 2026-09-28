param(
    [Parameter(Mandatory = $true)]
    [string]$HealthUrl,

    [ValidateRange(1, 1)]
    [int]$Threads = 1,

    [ValidateRange(1, 30)]
    [int]$RampSeconds = 1,

    [ValidateRange(10, 60)]
    [int]$DurationSeconds = 20,

    [string]$JMeterCommand = 'jmeter',

    [string]$AllowedHost,

    [switch]$IConfirmAuthorizedTarget
)

$ErrorActionPreference = 'Stop'
$uri = [Uri]$HealthUrl
if (-not $uri.IsAbsoluteUri -or $uri.AbsolutePath -ne '/health') {
    throw 'HealthUrl must be an absolute URL ending in /health.'
}
if (-not $uri.IsLoopback) {
    if ($uri.Scheme -ne 'https') {
        throw 'Non-loopback health targets must use HTTPS.'
    }
    if (-not $IConfirmAuthorizedTarget -or -not $AllowedHost -or $AllowedHost -ne $uri.Host) {
        throw 'Provide the exact AllowedHost and explicit authorization for a remote health target.'
    }
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outputDirectory = Join-Path $PSScriptRoot "../tmp/jmeter-health-$timestamp"
$resultFile = Join-Path $outputDirectory 'results.jtl'
$reportDirectory = Join-Path $outputDirectory 'report'
$testPlan = Join-Path $PSScriptRoot 'jmeter/api-health-load.jmx'
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null

# A single paced visitor keeps the test below the deployed API Gateway rate limit.
& $JMeterCommand `
    -n `
    -t $testPlan `
    "-Jprotocol=$($uri.Scheme)" `
    "-Jhost=$($uri.Host)" `
    "-Jport=$($uri.Port)" `
    "-Jthreads=$Threads" `
    "-Jramp_seconds=$RampSeconds" `
    "-Jduration_seconds=$DurationSeconds" `
    -l $resultFile `
    -e `
    -o $reportDirectory

if ($LASTEXITCODE -ne 0) {
    throw "JMeter failed with exit code $LASTEXITCODE."
}

$rows = Import-Csv $resultFile
$failures = @($rows | Where-Object { $_.success -ne 'true' })
if ($failures.Count -gt 0) {
    throw "JMeter recorded $($failures.Count) failed health requests."
}

$average = [math]::Round(($rows | Measure-Object -Property elapsed -Average).Average, 1)
$maximum = ($rows | Measure-Object -Property elapsed -Maximum).Maximum
Write-Output "JMeter health profile passed: $($rows.Count) requests, 0 failures, ${average}ms average, ${maximum}ms maximum."
Write-Output "HTML report: $reportDirectory/index.html"
