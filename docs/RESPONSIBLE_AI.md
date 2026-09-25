# Responsible AI — StaySphere Price Estimator

## What the model does

Predicts an estimated nightly listing price from a small set of
listing characteristics (city, property type, room type, accommodates,
bedrooms, minimum nights, review rating), trained via
`analytics/train_price_model.py`. Chosen model: whichever of Linear
Regression or Random Forest scores lower RMSE on a held-out test split
(currently Random Forest — see `evidence/test-data-ai.md` for
actual metrics).

## Limitations

- **Trained on synthetic/sample data.** As of this writing the real
  Kaggle dataset has not been downloaded, so all current metrics
  reflect a synthetic dataset generated to match the documented schema,
  not real market data. This must be re-evaluated once the real dataset
  is used (see `data/DATA_DICTIONARY.md`).
- **Historical data does not guarantee future prices.** Prices are
  influenced by seasonality, demand, and market conditions the model
  does not observe.
- **Data may represent specific cities/time periods** and may not
  generalize to locations or time periods outside what it was trained on.
- **Missing data can affect predictions.** Rows with missing values in
  the feature columns are dropped during training, which can bias the
  model toward listings with more complete data.
- **Correlation does not imply causation.** A feature's importance in
  the model reflects a statistical association with price in the
  training data, not necessarily a causal driver of price.
- **Model performance may vary by city/property type** not well
  represented in the training data.
- **Predictions are estimates, not guarantees**, and should not be used
  for real pricing decisions. The API response includes this disclaimer
  directly (`disclaimer` field in `/api/ml/price-estimate`).

## How this is communicated to users

The frontend's Price Estimator page states upfront that this is an
academic estimate, not a real pricing tool, and every API response
includes a `disclaimer` field and a `range_low`/`range_high` band
(rather than a single falsely-precise number) derived from the model's
mean absolute error on the test set.

## The recommendation engine ("Find your match")

`/api/recommendations` ranks listings using a **simple, explicit
weighted-scoring rule** (budget fit, estimated value, rating, capacity
match — see `src/backend/app/routers/recommendations.py`), not a learned
recommender model. The "estimated value" component reuses the same
trained price model described above, so its limitations apply here too.

- **Rankings can reflect historical data bias.** Listings with higher
  ratings or more complete data will rank higher regardless of whether
  that reflects genuine quality.
- **"Great value" is model-relative, not guaranteed.** A listing flagged
  as a good deal is priced below what the model expects for its
  features — that does not verify the listing's actual condition,
  safety, or accuracy of its description.
- **Not a personalized recommender.** It does not learn from individual
  user behaviour or history — every user with the same inputs gets the
  same ranking. This is intentional and disclosed in the API response's
  `disclaimer` field and in the frontend copy.
- **Popularity/exposure bias.** Ranking by a fixed formula means the
  same listings will surface repeatedly for similar searches, which can
  concentrate bookings on a small set of listings rather than
  distributing exposure evenly.

## Fairness considerations

The training features do not include any protected attribute (e.g. host
name, host photo, guest identity). `neighbourhood`/`city` are legitimate,
commonly-used real-estate pricing features, but the team acknowledges
that location-based pricing models can encode and perpetuate existing
geographic price disparities. This is flagged here rather than addressed
with a specific fairness intervention, given the project's academic
scope and synthetic data.
