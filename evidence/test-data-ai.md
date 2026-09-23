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
