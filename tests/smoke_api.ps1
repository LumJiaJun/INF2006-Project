param(
    [Parameter(Mandatory = $true)]
    [string]$FrontendUrl,

    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl
)

$ErrorActionPreference = 'Stop'

$expectedAssets = @{
    'index.html' = 'text/html'
    'styles.css' = 'text/css'
    'app.js' = 'application/javascript'
    'auth.js' = 'application/javascript'
    'auth-config.js' = 'application/javascript'
    'model-options.json' = 'application/json'
}

foreach ($asset in $expectedAssets.GetEnumerator()) {
    $assetResponse = Invoke-WebRequest `
        -Uri "$FrontendUrl/$($asset.Key)" `
        -UseBasicParsing

    if ($assetResponse.StatusCode -ne 200 -or -not $assetResponse.Headers['Content-Type'].StartsWith($asset.Value)) {
        throw "$($asset.Key) did not return the expected content type."
    }
}

$healthResponse = Invoke-WebRequest `
    -Uri "$ApiBaseUrl/health" `
    -Headers @{ Origin = $FrontendUrl } `
    -UseBasicParsing
$healthBody = $healthResponse.Content | ConvertFrom-Json

if ($healthResponse.StatusCode -ne 200 -or $healthBody.status -ne 'healthy') {
    throw 'Health check did not return the expected response.'
}

$predictionPayload = @{
    city = 'Paris'
    neighbourhood = 'Buttes-Montmartre'
    property_type = 'Entire apartment'
    room_type = 'Entire place'
    instant_bookable = $false
    host_is_superhost = $false
    host_identity_verified = $false
    latitude = 48.88668
    longitude = 2.33343
    accommodates = 2
    bedrooms = 1
    minimum_nights = 2
    review_scores_rating = 100
    host_total_listings_count = 1
    amenities_count = 5
} | ConvertTo-Json -Compress

$predictionResponse = Invoke-WebRequest `
    -Uri "$ApiBaseUrl/predict" `
    -Method Post `
    -Headers @{ Origin = $FrontendUrl } `
    -ContentType 'application/json' `
    -Body $predictionPayload `
    -UseBasicParsing
$predictionBody = $predictionResponse.Content | ConvertFrom-Json

if ($predictionResponse.StatusCode -ne 200 -or -not $predictionBody.estimated_nightly_price) {
    throw 'Prediction did not return the expected response.'
}

foreach ($protectedRoute in @(
    @{ Method = 'GET'; Path = 'history'; Body = $null },
    @{ Method = 'POST'; Path = 'predictions'; Body = $predictionPayload }
)) {
    try {
        $parameters = @{
            Uri = "$ApiBaseUrl/$($protectedRoute.Path)"
            Method = $protectedRoute.Method
            Headers = @{ Origin = $FrontendUrl }
            UseBasicParsing = $true
        }
        if ($protectedRoute.Body) {
            $parameters.ContentType = 'application/json'
            $parameters.Body = $protectedRoute.Body
        }
        Invoke-WebRequest @parameters | Out-Null
        throw "$($protectedRoute.Path) unexpectedly allowed an unauthenticated request."
    } catch {
        if ([int]$_.Exception.Response.StatusCode -ne 401) {
            throw
        }
    }
}

try {
    Invoke-WebRequest `
        -Uri "$ApiBaseUrl/predict" `
        -Method Post `
        -Headers @{ Origin = $FrontendUrl } `
        -ContentType 'application/json' `
        -Body '{' `
        -UseBasicParsing | Out-Null
    throw 'Malformed JSON unexpectedly succeeded.'
} catch {
    if ([int]$_.Exception.Response.StatusCode -ne 400) {
        throw
    }
}

Write-Output 'Health check passed.'
Write-Output 'Frontend asset checks passed.'
Write-Output "Prediction passed: $($predictionBody.estimated_nightly_price) $($predictionBody.currency)."
Write-Output 'Protected route authentication checks passed.'
Write-Output 'Malformed request validation passed.'
