param(
    [string]$EvidencePath = 'tmp/cloud-verification.md',
    [string]$AlertEmail = '',
    [switch]$IConfirmAuthorizedTarget
)

$ErrorActionPreference = 'Stop'

if (-not $IConfirmAuthorizedTarget) {
    throw 'Pass -IConfirmAuthorizedTarget only for an AWS account you are authorized to test.'
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$terraformDirectory = Join-Path $repositoryRoot 'src/infrastructure'
$planPath = Join-Path $repositoryRoot 'tmp/cloud-verification.tfplan'
$evidenceFile = Join-Path $repositoryRoot $EvidencePath
$previousAlertEmail = $env:TF_VAR_alert_email
$planVerified = $false

function Invoke-Native {
    param(
        [string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )
    $output = & $Command @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "$Command failed with exit code $LASTEXITCODE.`n$($output -join "`n")"
    }
    return $output
}

function Terraform-Output {
    param([string]$Name)
    return ((Invoke-Native -Command 'terraform' -Arguments @(("-chdir=" + $terraformDirectory), 'output', '-raw', $Name)) -join '').Trim()
}

try {
    if ($AlertEmail) {
        $env:TF_VAR_alert_email = $AlertEmail
    } else {
        Remove-Item Env:TF_VAR_alert_email -ErrorAction SilentlyContinue
    }

    Invoke-Native -Command 'terraform' -Arguments @(("-chdir=" + $terraformDirectory), 'fmt', '-check', '-recursive') | Out-Null
    Invoke-Native -Command 'terraform' -Arguments @(("-chdir=" + $terraformDirectory), 'validate', '-no-color') | Out-Null

    & terraform "-chdir=$terraformDirectory" plan -detailed-exitcode -input=false -no-color "-out=$planPath" | Out-Null
    $planExitCode = $LASTEXITCODE
    if ($planExitCode -eq 1) {
        throw 'Terraform plan failed.'
    }
    if ($planExitCode -eq 2) {
        throw 'Terraform detected changes. Review the plan before treating the deployment as verified.'
    }
    $planVerified = $true

    $frontendUrl = Terraform-Output 'frontend_url'
    $healthUrl = Terraform-Output 'health_url'
    $apiBaseUrl = $healthUrl -replace '/health$', ''
    $smokeOutput = & (Join-Path $PSScriptRoot 'smoke_api.ps1') -FrontendUrl $frontendUrl -ApiBaseUrl $apiBaseUrl
    if ($LASTEXITCODE -ne 0) {
        throw 'The deployed smoke test failed.'
    }

    $resourceCount = (Invoke-Native -Command 'terraform' -Arguments @(("-chdir=" + $terraformDirectory), 'state', 'list')).Count
    $historyTable = Terraform-Output 'prediction_history_table_name'
    $namePrefix = $historyTable -replace '-prediction-history$', ''
    $lambdaResults = foreach ($suffix in @('health', 'prediction', 'analytics', 'history', 'chat')) {
        $configuration = Invoke-Native -Command 'aws' -Arguments @(
            'lambda', 'get-function-configuration',
            '--function-name', "$namePrefix-$suffix",
            '--query', '[State,LastUpdateStatus,length(VpcConfig.SubnetIds)]',
            '--output', 'text'
        )
        $parts = (($configuration -join '') -split "`t")
        [pscustomobject]@{
            Name = $suffix
            State = $parts[0]
            Update = $parts[1]
            Subnets = [int]$parts[2]
        }
    }
    $lambdaHealthy = @($lambdaResults | Where-Object {
        $_.State -ne 'Active' -or $_.Update -ne 'Successful' -or $_.Subnets -ne 2
    }).Count -eq 0

    $alarmStates = Invoke-Native -Command 'aws' -Arguments @(
        'cloudwatch', 'describe-alarms', '--alarm-name-prefix', $namePrefix,
        '--query', 'MetricAlarms[].StateValue', '--output', 'text'
    )
    $alarmValues = (($alarmStates -join "`t") -split "`t") | Where-Object { $_ }
    $alarmsHealthy = @($alarmValues | Where-Object { $_ -ne 'OK' }).Count -eq 0

    $trailName = Terraform-Output 'cloudtrail_name'
    $trailStatus = Invoke-Native -Command 'aws' -Arguments @(
        'cloudtrail', 'get-trail-status', '--name', $trailName,
        '--query', '[IsLogging,LatestDeliveryError]', '--output', 'text'
    )
    $trailParts = (($trailStatus -join '') -split "`t")
    $trailHealthy = $trailParts[0] -eq 'True' -and $trailParts[1] -in @('None', '')

    $backupStatus = Invoke-Native -Command 'aws' -Arguments @(
        'dynamodb', 'describe-continuous-backups', '--table-name', $historyTable,
        '--query', 'ContinuousBackupsDescription.[ContinuousBackupsStatus,PointInTimeRecoveryDescription.PointInTimeRecoveryStatus]',
        '--output', 'text'
    )
    $backupParts = (($backupStatus -join '') -split "`t")
    $backupHealthy = $backupParts[0] -eq 'ENABLED' -and $backupParts[1] -eq 'ENABLED'

    $glueJob = Terraform-Output 'glue_transform_job_name'
    $glueStatus = ((Invoke-Native -Command 'aws' -Arguments @(
        'glue', 'get-job-runs', '--job-name', $glueJob, '--max-results', '1',
        '--query', 'JobRuns[0].JobRunState', '--output', 'text'
    )) -join '').Trim()

    $frontendBucket = Terraform-Output 'frontend_bucket_name'
    $dataBucket = Terraform-Output 'data_lake_bucket_name'
    $privateBuckets = $true
    foreach ($bucket in @($frontendBucket, $dataBucket)) {
        $publicAccess = Invoke-Native -Command 'aws' -Arguments @(
            's3api', 'get-public-access-block', '--bucket', $bucket,
            '--query', 'PublicAccessBlockConfiguration.[BlockPublicAcls,IgnorePublicAcls,BlockPublicPolicy,RestrictPublicBuckets]',
            '--output', 'text'
        )
        $values = (($publicAccess -join '') -split "`t")
        if (@($values | Where-Object { $_ -ne 'True' }).Count -ne 0) {
            $privateBuckets = $false
        }
    }

    $distributionId = Terraform-Output 'cloudfront_distribution_id'
    $webAcl = ((Invoke-Native -Command 'aws' -Arguments @(
        'cloudfront', 'get-distribution', '--id', $distributionId,
        '--query', 'Distribution.DistributionConfig.WebACLId', '--output', 'text'
    )) -join '').Trim()
    $wafAttached = $webAcl -notin @('', 'None')

    $topicArn = Terraform-Output 'operational_alerts_topic_arn'
    $subscriptionCount = [int](((Invoke-Native -Command 'aws' -Arguments @(
        'sns', 'list-subscriptions-by-topic', '--topic-arn', $topicArn,
        '--query', "length(Subscriptions[?SubscriptionArn!='PendingConfirmation'])", '--output', 'text'
    )) -join '').Trim())

    $allChecksPassed = $lambdaHealthy -and $alarmsHealthy -and $trailHealthy -and
        $backupHealthy -and $glueStatus -eq 'SUCCEEDED' -and $privateBuckets -and $wafAttached
    if (-not $allChecksPassed) {
        throw 'One or more deployed control checks failed.'
    }

    $evidenceDirectory = Split-Path -Parent $evidenceFile
    New-Item -ItemType Directory -Force -Path $evidenceDirectory | Out-Null
    $smokeLines = ($smokeOutput | ForEach-Object { "  - $_" }) -join "`n"
    $lambdaLines = ($lambdaResults | ForEach-Object {
        "  - $($_.Name): state $($_.State), update $($_.Update), private subnet count $($_.Subnets)"
    }) -join "`n"
    $content = @"
# Redacted cloud verification

- **Objective:** Reproduce the deployed functional and control checks without recording account IDs, resource IDs, URLs, email addresses, tokens, or credentials.
- **Setup:** Authorized AWS credentials, initialized Terraform working directory, and the Terraform-managed development stack in ``ap-southeast-1``.
- **Command:** ``./tests/verify_cloud.ps1 -EvidencePath "$EvidencePath" -IConfirmAuthorizedTarget``
- **Expected result:** Terraform reports no drift; the public workflow passes; all Lambdas are active in two private subnets; alarms are OK; CloudTrail is logging; DynamoDB recovery is enabled; the latest Glue run succeeded; both S3 buckets block public access; and WAF remains attached to CloudFront.
- **Actual result:** Passed on $(Get-Date -Format 'yyyy-MM-dd'). Terraform managed $resourceCount resources and returned detailed exit code 0.

## Functional workflow

$smokeLines

## Deployed control summary

$lambdaLines
  - CloudWatch alarms: $($alarmValues.Count) checked, all OK
  - CloudTrail: logging enabled with no latest delivery error
  - DynamoDB: continuous backups and point-in-time recovery enabled
  - Glue: latest transform run $glueStatus
  - S3: frontend and data-lake public access blocks fully enabled
  - CloudFront: WAF web ACL attached
  - SNS: $subscriptionCount confirmed subscription(s); zero means delivery is not currently active

## Interpretation

This verifies the current single-region development deployment at the tested time. It does not prove unlimited scale, multi-region recovery, authenticated multi-user isolation, or future drift-free operation. The generated evidence intentionally excludes cloud identifiers and operator contact details.

- **Artefact paths:** ``tests/verify_cloud.ps1``, ``tests/smoke_api.ps1``, ``src/infrastructure``, and this file.
"@
    Set-Content -LiteralPath $evidenceFile -Value $content -Encoding utf8
    Write-Output "Cloud verification passed. Redacted evidence written to $EvidencePath."
} finally {
    if ($planVerified) {
        Remove-Item -LiteralPath $planPath -Force -ErrorAction SilentlyContinue
    }
    if ($null -eq $previousAlertEmail) {
        Remove-Item Env:TF_VAR_alert_email -ErrorAction SilentlyContinue
    } else {
        $env:TF_VAR_alert_email = $previousAlertEmail
    }
}
