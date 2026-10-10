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

- **Objective:** Compare a simple baseline and two candidate regressors on a held-out evaluation partition, then select using a currency-aware aggregate criterion. The same held-out partition is used for candidate selection and the reported final metrics, so it is not a separate untouched final test set and the figures may be slightly optimistic.
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
- **Interpretation:** The frontend also reports each city's average-to-median price ratio. This is a currency-neutral within-city shape indicator, not an exchange-rate conversion or cross-city price ranking.
- **Date:** 2026-09-23
- **Artefact path:** `evidence/data-pipeline.md`

## Offline submission reproduction

- **Objective:** Confirm that a marker can execute preprocessing, all candidate models, evaluation, model selection, and export without AWS credentials or the excluded full dataset.
- **Setup:** Pinned test dependencies and the committed 500-row deterministic synthetic sample.
- **Command / steps:** Run `python tests/local_preflight.py --include-ml` from the repository root.
- **Expected result:** Unit tests, source checks, manifest validation, Terraform validation where initialized, and synthetic end-to-end model training all complete successfully.
- **Actual result:** Passed again on 2026-10-04. All 47 unit tests (7 October 2026 count; earlier runs recorded 46) passed, 15 manifest paths resolved, frontend syntax and Terraform checks passed, and histogram gradient boosting was selected from 390 scoped training rows and 98 test rows. The synthetic score is deliberately excluded from real-world quality claims.
- **Date:** 2026-10-04
- **Artefact path:** `tests/local_preflight.py`, `analytics/generate_sample_data.py`, `data/sample/listings_synthetic.csv`, and `evidence/rubric-gap-review-2026-10-02.md`

## Submitted artefact consistency

- **Objective:** Prevent silent disagreement between the profiled source, evaluated model, model-selection rule, frontend validation options, synthetic sample, and data dictionary.
- **Setup:** Committed JSON artefacts, frontend model options, data documentation, and deterministic sample generator.
- **Command / steps:** Run `python -m unittest discover -s tests -p "test_submission_data.py" -v`.
- **Expected result:** Source hashes match; the declared model has the lowest recorded selection metric; every frontend city, neighbourhood, coordinate range and price boundary matches the evaluation; the synthetic sample regenerates byte-for-byte with 50 rows for each city; and every model input is documented.
- **Actual result:** Passed all five consistency tests on 2026-10-04.
- **Date:** 2026-10-04
- **Artefact path:** `tests/test_submission_data.py`, `analytics/artifacts/data_profile.json`, `analytics/artifacts/model_evaluation.json`, `src/frontend/model-options.json`, and `data/DATA_DICTIONARY.md`

## Full-dataset deterministic replay

- **Objective:** Verify that the supplied full-data training command reproduces the committed evaluation and deployable model rather than only completing successfully.
- **Setup:** The hash-verified 279,712-row `Listings.csv`, pinned analytics dependencies, and ignored temporary output paths.
- **Command / steps:** Run `python tests/verify_full_model.py --listings "data/raw/Airbnb Data/Listings.csv"`.
- **Expected result:** Every compared value matches exactly.
- **Actual result:** Passed on 2026-10-04. All seven comparisons matched exactly, including every candidate metric and the exported model hash.
- **Date:** 2026-10-04
- **Artefact path:** `tests/verify_full_model.py`, `analytics/train_model.py`, `analytics/artifacts/model_evaluation.json`, and `data/README.md`
