# Test 3 — Data / AI Validation Test

**Objective:** prove the price estimator was trained and evaluated on a
held-out test set with real metrics, and that the API endpoint using it
produces an interpretable, bounded estimate.

**Dataset used:** `data/sample/dummy_listings.csv` (600 synthetic rows,
see `data/DATA_DICTIONARY.md`). **This is synthetic data, not the real
Kaggle dataset**, because the real dataset has not been downloaded yet.
Metrics below describe model behaviour on this synthetic data only and
will change once trained on the real dataset.

**Method:** `analytics/train_price_model.py` — 80/20 train/test split,
Linear Regression baseline vs Random Forest Regressor, evaluated with
MAE, RMSE, R².

**Command:**
```
cd analytics
python3 train_price_model.py
cd ../tests
pytest 03_data_ai -v
```

**Actual metrics (captured 2026-09-22, run against dummy_listings.csv after
the city-coordinate fix described in `AI_USE_DECLARATION.md`, n=600, 80/20
split, n_test=120):**

| Model | MAE | RMSE | R² |
|---|---|---|---|
| Linear Regression (baseline) | 18.07 | 21.67 | 0.868 |
| Random Forest Regressor | 18.17 | 21.90 | 0.865 |

Linear Regression was selected this run (marginally lower RMSE). Full
numbers in `analytics/figures/metrics.json`. Actual-vs-predicted and
residual plots in `analytics/figures/actual_vs_predicted.png` and
`analytics/figures/residuals.png`. Note: the specific numbers shift
slightly whenever the underlying data changes (as they did here, when a
coordinate-generation bug was fixed) — this is expected and is exactly
why the pipeline re-evaluates from scratch each run rather than hardcoding
a result.

**Test cases and results:**

| Test | Expected result | Actual result |
|---|---|---|
| `test_model_artifact_exists` | Trained model file present | PASS |
| `test_metrics_file_has_required_fields` | metrics.json has MAE/RMSE/R² for both models | PASS |
| `test_figures_generated` | actual-vs-predicted and residual plots exist | PASS |
| `test_price_estimate_endpoint_returns_interpretable_output` | API returns price + range + key factors + disclaimer | PASS |
| `test_price_estimate_rejects_invalid_input` | Invalid input (negative accommodates) rejected with 422 | PASS |
| `test_booking_made_by_guest_is_visible_to_admin` | A booking a guest makes is visible to an admin via `/api/admin/bookings` (proves shared-database persistence, not per-session state) | PASS |

**Actual output (captured 2026-09-22, see `evidence/pytest-output.txt` for the full 26-test run):**
```
03_data_ai/test_data_ai.py::test_model_artifact_exists PASSED
03_data_ai/test_data_ai.py::test_metrics_file_has_required_fields PASSED
03_data_ai/test_data_ai.py::test_figures_generated PASSED
03_data_ai/test_data_ai.py::test_price_estimate_endpoint_returns_interpretable_output PASSED
03_data_ai/test_data_ai.py::test_price_estimate_rejects_invalid_input PASSED
03_data_ai/test_data_ai.py::test_booking_made_by_guest_is_visible_to_admin PASSED
6 passed
```

**Date:** 2026-09-21
**Artefact path:** `evidence/test-data-ai.md` (this file),
`analytics/figures/metrics.json`, `analytics/figures/*.png`

**Limitations:**
- Trained on synthetic data, not the real Kaggle dataset — an R² this high
  is partly because the synthetic price generator itself is a fairly clean
  linear-ish function of the same features used to predict it. Expect a
  lower, more realistic R² once trained on the real dataset, which will have
  more noise and unmodelled factors.
- No cross-validation, only a single train/test split.
- Model does not account for seasonality, demand, or competitor pricing.
- See `docs/RESPONSIBLE_AI.md` for full limitations and responsible-use notes.

**NOT YET EXECUTED:** retraining and re-evaluating on the real Kaggle dataset
once downloaded and inspected.
