param(
    [Parameter(Mandatory = $true)]
    [string]$TableName,

    [Parameter(Mandatory = $true)]
    [string]$ChatFunctionName,

    [ValidateSet('ap-southeast-1')]
    [string]$Region = 'ap-southeast-1',

    [switch]$IConfirmAuthorizedTarget
)

$ErrorActionPreference = 'Stop'

if (-not $IConfirmAuthorizedTarget) {
    throw 'Use -IConfirmAuthorizedTarget only for an AWS environment you own or are authorized to test.'
}

# Each run uses a unique synthetic user and removes its only test record in finally.
$runId = [Guid]::NewGuid().ToString('N')
$testUserId = "integration-test-$runId"
$createdAt = (Get-Date).ToUniversalTime().ToString('o')
$sortKey = "$createdAt#$runId"
$temporaryDirectory = Join-Path $PSScriptRoot "../tmp/chat-integration-$runId"
$itemFile = Join-Path $temporaryDirectory 'item.json'
$keyFile = Join-Path $temporaryDirectory 'key.json'
$eventFile = Join-Path $temporaryDirectory 'event.json'
$responseFile = Join-Path $temporaryDirectory 'lambda-response.json'
New-Item -ItemType Directory -Path $temporaryDirectory -Force | Out-Null

$item = @{
    user_id                  = @{ S = $testUserId }
    created_at_prediction_id = @{ S = $sortKey }
    created_at               = @{ S = $createdAt }
    city                     = @{ S = 'Paris' }
    neighbourhood            = @{ S = 'Louvre' }
    property_type            = @{ S = 'Entire apartment' }
    room_type                = @{ S = 'Entire place' }
    accommodates             = @{ N = '2' }
    bedrooms                 = @{ N = '1' }
    minimum_nights           = @{ N = '2' }
    predicted_price          = @{ N = '123.45' }
    currency                 = @{ S = 'EUR' }
    model_version            = @{ S = 'integration-test' }
} | ConvertTo-Json -Depth 5 -Compress
$key = @{
    user_id                  = @{ S = $testUserId }
    created_at_prediction_id = @{ S = $sortKey }
} | ConvertTo-Json -Depth 4 -Compress

$event = @{
    body = (@{ message = 'What is my most recent saved prediction?'; page = 'index.html' } | ConvertTo-Json -Compress)
    requestContext = @{
        requestId = "chat-integration-$runId"
        authorizer = @{ jwt = @{ claims = @{ sub = $testUserId } } }
    }
} | ConvertTo-Json -Depth 8 -Compress

[System.IO.File]::WriteAllText($itemFile, $item, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($keyFile, $key, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($eventFile, $event, [System.Text.UTF8Encoding]::new($false))
$recordCreated = $false

try {
    & aws dynamodb put-item --table-name $TableName --region $Region --item "file://$itemFile" --condition-expression 'attribute_not_exists(user_id)'
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the isolated DynamoDB test record.' }
    $recordCreated = $true

    & aws lambda invoke --function-name $ChatFunctionName --region $Region --cli-binary-format raw-in-base64-out --payload "fileb://$eventFile" $responseFile | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'The chat Lambda invocation failed.' }

    $lambdaResponse = Get-Content $responseFile -Raw | ConvertFrom-Json
    if ([int]$lambdaResponse.statusCode -ne 200) {
        throw "Chat Lambda returned HTTP $($lambdaResponse.statusCode)."
    }
    $body = $lambdaResponse.body | ConvertFrom-Json
    if (-not $body.reply -or $body.reply.Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries).Count -gt 120) {
        throw 'Chat Lambda returned an empty or unbounded reply.'
    }

    # The handler logs only the test request ID and retrieved-record count, never the prompt or record fields.
    $completion = @()
    for ($attempt = 1; $attempt -le 6 -and $completion.Count -eq 0; $attempt++) {
        $logEvents = & aws logs filter-log-events --log-group-name "/aws/lambda/$ChatFunctionName" --region $Region --filter-pattern 'chat_completed' --query 'events[].message' --output json | ConvertFrom-Json
        $completion = @($logEvents | ForEach-Object {
            $envelope = $_ | ConvertFrom-Json
            $message = $envelope.message | ConvertFrom-Json
            if ($message.request_id -eq "chat-integration-$runId" -and $message.history_record_count -eq 1) {
                $message
            }
        })
        if ($completion.Count -eq 0) {
            Start-Sleep -Seconds 5
        }
    }
    if ($completion.Count -eq 0) {
        throw 'The expected one-record chat completion telemetry was not found.'
    }

    Write-Output "Chat integration passed: Bedrock returned a bounded reply after the Lambda retrieved 1 isolated DynamoDB record."
} finally {
    if ($recordCreated) {
        & aws dynamodb delete-item --table-name $TableName --region $Region --key "file://$keyFile" | Out-Null
    }
    if ($recordCreated -and $LASTEXITCODE -ne 0) {
        Write-Warning 'The disposable DynamoDB record could not be deleted. Use the run ID shown in the temporary path to investigate.'
    }
}
