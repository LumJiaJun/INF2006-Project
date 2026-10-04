# Prediction Lambda

The prediction runtime validates an API Gateway request, transforms JSON fields into the trained schema, runs the exported scikit-learn pipeline, and returns a nightly price estimate in the selected city's local currency.

## Why a container image

The measured local inference dependencies totalled approximately 258 MB before the model, metadata, and package metadata. This exceeds Lambda's 250 MB unzipped limit for ZIP packages and layers. A Lambda container image is therefore used for measured package-size reasons, not as a general project default.

## Build

Build from the repository root:

```powershell
docker build --platform linux/amd64 --provenance=false `
  -f src/backend/predict/Dockerfile `
  -t airbnb-prediction:1.0.3 .
```

The complete model artifact must first exist at
`analytics/artifacts/airbnb_price_model.joblib`. It is intentionally excluded
from Git and must be reproduced from the CC0 source data or downloaded from the
authorized deployment artefact location.

For a clean-checkout container smoke build, first generate a non-production
model from the committed synthetic sample:

```powershell
python -m pip install -r tests/requirements.txt
python analytics/train_model.py `
  --listings data/sample/listings_synthetic.csv `
  --model-output analytics/artifacts/airbnb_price_model.joblib `
  --metrics-output tmp/sample-container-metrics.json
docker build --platform linux/amd64 --provenance=false `
  -f src/backend/predict/Dockerfile `
  -t airbnb-prediction:sample-smoke .
```

This proves that the Lambda image can be assembled with the same pipeline
shape. The synthetic model is not the evaluated deployment model and its
metrics must not be reported as real-world performance.

## Request contract

Required fields:

- `city`, `neighbourhood`, `property_type`, and `room_type`
- `latitude` and `longitude`
- `accommodates` and `minimum_nights`
- `instant_bookable`, `host_is_superhost`, and `host_identity_verified`
- `host_total_listings_count` and `amenities_count`

Optional nullable fields:

- `bedrooms`
- `review_scores_rating`

The handler rejects unknown fields, unsupported categories, invalid city-neighbourhood combinations, coordinates outside the selected city's observed range, and unreasonable numeric values.
