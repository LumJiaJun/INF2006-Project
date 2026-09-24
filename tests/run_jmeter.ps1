param(
    [Parameter(Mandatory = $true)]
    [string]$FrontendUrl,

    [ValidateRange(1, 100)]
    [int]$Threads = 10,

    [ValidateRange(1, 300)]
    [int]$RampSeconds = 10,

    [ValidateRange(5, 600)]
    [int]$DurationSeconds = 30,

    [string]$JMeterCommand = 'jmeter'
)

$ErrorActionPreference = 'Stop'
$uri = [Uri]$FrontendUrl
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outputDirectory = Join-Path $PSScriptRoot "../tmp/jmeter-$timestamp"
$resultFile = Join-Path $outputDirectory 'results.jtl'
$reportDirectory = Join-Path $outputDirectory 'report'
$testPlan = Join-Path $PSScriptRoot 'jmeter/web-load.jmx'
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null

# Non-GUI mode produces repeatable result data without desktop overhead.
& $JMeterCommand `
    -n `
    -t $testPlan `
    "-Jprotocol=$($uri.Scheme)" `
    "-Jhost=$($uri.Host)" `
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
    throw "JMeter recorded $($failures.Count) failed requests."
}

$average = [math]::Round(($rows | Measure-Object -Property elapsed -Average).Average, 1)
$maximum = ($rows | Measure-Object -Property elapsed -Maximum).Maximum
Write-Output "JMeter passed: $($rows.Count) requests, 0 failures, ${average}ms average, ${maximum}ms maximum."
Write-Output "HTML report: $reportDirectory/index.html"
