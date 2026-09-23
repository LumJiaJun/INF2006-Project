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
```

## Method, evaluation and limitations

- Method: Dataset profiling is implemented. Model selection follows after target and feature quality review.
- Evaluation: Candidate models will be compared on the same held-out split using MAE, RMSE, and R-squared.
- Limitations: The source represents historical listings across multiple cities and currencies. Reviews has no text field, so sentiment analysis is unsupported.
