# Analytics / ML

## Contents

- `train_price_model.py` — trains and evaluates the nightly price
  estimator (Linear Regression baseline vs Random Forest), saves the
  winning model bundle to `../src/backend/app/ml_model/price_model.joblib`
  and evaluation artefacts to `figures/`.
- `figures/` — `metrics.json`, `actual_vs_predicted.png`,
  `residuals.png`, `feature_importance.png` (generated, not committed
  by hand — regenerate any time by re-running the script).
- `requirements.txt` — Python deps for this folder (superset already
  covered by `src/backend/requirements.txt`, listed separately so
  `analytics/` can be run standalone).

## Running it

```
cd analytics
pip install -r requirements.txt
python3 train_price_model.py                      # uses data/sample/dummy_listings.csv
python3 train_price_model.py ../data/raw/real.csv  # once the real dataset is downloaded
```

## Method summary

- **Target:** `price`
- **Features:** `city`, `property_type`, `room_type`, `accommodates`,
  `bedrooms`, `minimum_nights`, `review_scores_rating`. No identifier
  columns (listing_id, host_id) are used as predictive features, and no
  feature is derived from the target (avoiding data leakage).
- **Preprocessing:** drop duplicate `listing_id`s, drop rows with
  missing values in the feature/target columns, label-encode
  categorical features.
- **Split:** 80/20 train/test, `random_state=42`.
- **Models compared:** Linear Regression (baseline), Random Forest
  Regressor (200 trees, max depth 10). The one with lower test-set RMSE
  is saved as the serving model.
- **Metrics:** MAE, RMSE, R² on the held-out test set — see
  `evidence/test-data-ai.md` for actual numbers from the last run.

See `docs/RESPONSIBLE_AI.md` for limitations.
