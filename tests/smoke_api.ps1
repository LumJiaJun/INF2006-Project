param(
    [Parameter(Mandatory = $true)]
    [string]$FrontendUrl,

    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl
)

$ErrorActionPreference = 'Stop'

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
Write-Output "Prediction passed: $($predictionBody.estimated_nightly_price) $($predictionBody.currency)."
Write-Output 'Malformed request validation passed.'
