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

## Method, evaluation and limitations

- Method: A city-stratified 80/20 split compares a median baseline, regularized linear regression, and histogram gradient boosting. All models learn `log1p(price)`. Categorical values are target encoded for gradient boosting, while numeric missing values are median-imputed. The selected model adds amenity count and known host attributes.
- Price scope: Thresholds are learned from the training partition only. V1 excludes each city's top 1% of prices to focus on the typical market and reduce extreme luxury-listing influence.
- Evaluation: Histogram gradient boosting was selected by median per-city normalized MAE. On 55,363 held-out rows it achieved MAE 191.836, RMSE 629.762, and R-squared 0.644 in pooled local-currency units. Log-price R-squared was 0.850. Per-city metrics are in `artifacts/model_evaluation.json` and are more interpretable than the pooled currency metrics.
- Limitations: Cities use different local currencies, historical prices may be stale, some important features are absent, missing values are imputed, and error remains material. Reviews has no text field, so sentiment analysis is unsupported.

Generated `.joblib` model files are intentionally excluded from Git. Recreate the model with the command above and verify its SHA-256 against `artifacts/model_evaluation.json`.
