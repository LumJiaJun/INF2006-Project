# Analytics and machine learning

Reproducible scripts for dataset inspection, preprocessing, model training, evaluation, and model export.

## What this produces

The pipeline will produce an evaluated nightly price estimator and supporting market summaries. Price outputs are estimates and are not guaranteed market prices.

## How to reproduce results

```bash
pip install -r requirements.txt
python profile_data.py \
  --listings "../data/raw/Airbnb Data/Listings.csv" \
  --reviews "../data/raw/Airbnb Data/Reviews.csv" \
  --output artifacts/data_profile.json

python train_model.py \
  --listings "../data/raw/Airbnb Data/Listings.csv" \
  --model-output artifacts/airbnb_price_model.joblib \
  --metrics-output artifacts/model_evaluation.json
```

For a safe submission-ZIP smoke test that does not require the 400 MB source
archive, run this from the repository root:

```bash
python tests/local_preflight.py --include-ml
```

This trains all candidate pipelines against the committed deterministic
synthetic sample and writes ignored outputs under `tmp/local-preflight/`. Its
metrics verify execution only and are not substitutes for the full-dataset
evaluation below.

## Method, evaluation and limitations

- Method: A city-stratified 80/20 split compares a global median baseline (one training-set median for all listings), regularized linear regression, and histogram gradient boosting. All models learn `log1p(price)`. Categorical values are target encoded for gradient boosting, while numeric missing values are median-imputed. The selected model adds amenity count and known host attributes.
- Price scope: Thresholds are learned from the training partition only. V1 excludes each city's top 1% of prices to focus on the typical market and reduce extreme luxury-listing influence.
- Evaluation: Histogram gradient boosting was selected by median per-city normalized MAE. On 55,363 held-out rows it achieved MAE 191.836, RMSE 629.762, and R-squared 0.644 in pooled local-currency units. Log-price R-squared was 0.850. Per-city metrics are in `artifacts/model_evaluation.json` and are more interpretable than the pooled currency metrics.
- Limitations: Cities use different local currencies, historical prices may be stale, some important features are absent, missing values are imputed, and error remains material. Reviews has no text field, so sentiment analysis is unsupported.

Generated `.joblib` model files are intentionally excluded from Git. Recreate the model with the command above and verify its SHA-256 against `artifacts/model_evaluation.json`.

## Cloud analytics transform

`glue_transform.py` is deployed as an AWS Glue 5.0 Spark job. It selects documented listing fields, removes invalid required values, applies a city-specific 99th-percentile price boundary, and writes city-partitioned Parquet. Terraform defines the corresponding projected Glue Catalog table and a governed Athena workgroup. The public analytics Lambda exposes only a fixed city-summary query; clients cannot submit SQL.

Deployment and run commands are documented in `src/infrastructure/README.md`. The measured run is recorded in `evidence/data-pipeline.md`.

## Decision-support categories

- Descriptive: city listing volume, average and median price, and rating.
- Diagnostic: distribution shape and cross-sectional associations between
  capacity, superhost status, and observed prices. These do not establish
  causation.
- Predictive: held-out price regression for a validated listing scenario.
- Prescriptive: cautious next-step prompts based on the prediction's position
  against its same-city median and browser-local scenario comparison. No
  occupancy, profit, or investment recommendation is produced.
