# Synthetic sample listings

`listings_synthetic.csv` contains 500 deterministic synthetic records generated
by `analytics/generate_sample_data.py`. It mirrors only the fields required by
the training pipeline and contains no scraped listings, identifiers, free text,
or personal data.

The sample exists to prove that the submitted preprocessing, model comparison,
evaluation, and export path runs offline. Its metrics are smoke-test results and
must not be reported as evidence of real-world model quality. The evaluated
project metrics remain those produced from the complete CC0 source dataset and
recorded in `analytics/artifacts/model_evaluation.json`.

Regenerate it from the repository root:

```bash
python analytics/generate_sample_data.py
```
