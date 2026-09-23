# Test: Data / AI validation

- **Objective:** Validate the source schema, target quality, missingness, review coverage, and whether review text exists before feature selection.
- **Setup:** Supplied `Listings.csv` and `Reviews.csv`, Python 3.11, and dependencies pinned in `analytics/requirements.txt`.
- **Command / steps:**
  ```powershell
  python analytics/profile_data.py `
    --listings "data/raw/Airbnb Data/Listings.csv" `
    --reviews "data/raw/Airbnb Data/Reviews.csv" `
    --output analytics/artifacts/data_profile.json
  ```
- **Expected result:** Produce a deterministic JSON profile containing file hashes, schemas, row counts, missingness, category counts, price distribution, and review date coverage.
- **Actual result:** Passed. The profile found 279,712 unique listings, 5,373,143 reviews, 113 non-positive prices, strong target skew, material missing ratings and bedrooms, 984 replacement characters from invalid UTF-8 sequences, and no review text field.
- **Date:** 2026-09-23
- **Artefact path:** `analytics/artifacts/data_profile.json`

## Model comparison

- **Objective:** Compare a simple baseline and two candidate regressors on an untouched test partition, then select using a currency-aware aggregate criterion.
- **Setup:** 279,599 eligible positive-price listings. Data is split 80/20 with city stratification. City-specific 99th-percentile limits are learned from the training partition, leaving 221,470 training rows and 55,363 test rows in the supported V1 scope.
- **Command / steps:**
  ```powershell
  python analytics/train_model.py `
    --listings "data/raw/Airbnb Data/Listings.csv" `
    --model-output analytics/artifacts/airbnb_price_model.joblib `
    --metrics-output analytics/artifacts/model_evaluation.json
  ```
- **Expected result:** Produce MAE, RMSE, and R-squared for every candidate, report per-city local-currency metrics, select the lowest median city-normalized MAE, and export the complete preprocessing and model pipeline.
- **Actual result:** Histogram gradient boosting outperformed the median and ridge baselines. On the supported held-out scope it achieved pooled MAE 191.836, RMSE 629.762, R-squared 0.644, log-price R-squared 0.850, and median city-normalized MAE 0.592. These results are moderate and must not be represented as high accuracy.
- **Date:** 2026-09-23
- **Artefact path:** `analytics/artifacts/model_evaluation.json`, `analytics/artifacts/model_evaluation_scoped_base.json`, and `analytics/artifacts/model_evaluation_untrimmed.json`

## Cloud analytical pipeline

- **Objective:** Validate that the cloud transform and fixed Athena query produce an interpretable market summary from the profiled listing fields.
- **Setup:** Encrypted raw listing object, Glue Spark transform, projected catalog partitions, and Athena workgroup.
- **Command / steps:** Follow `src/infrastructure/README.md` to upload `Listings.csv`, run Glue, and invoke `GET /analytics`.
- **Expected result:** Ten city partitions and ten summary records using each city's local currency and the documented supported-price scope.
- **Actual result:** Passed. Glue succeeded in 90 seconds, produced ten Parquet objects, and Athena returned ten summaries while scanning 566,077 bytes.
- **Date:** 2026-09-23
- **Artefact path:** `evidence/data-pipeline.md`
