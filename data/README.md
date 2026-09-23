# Data

The project uses an Airbnb listings and reviews archive supplied to the team. Raw files are deliberately excluded from Git because the combined size exceeds 400 MB.

## Dataset provenance

- Supplied archive: `archive (8).zip`
- Dataset: Airbnb Listings & Reviews by mysarahmadbhat on Kaggle
- Download URL: https://www.kaggle.com/datasets/mysarahmadbhat/airbnb-listings-reviews/data
- Licence: CC0 1.0 Public Domain, as declared on the Kaggle data card
- Coverage: 279,712 listings across 10 cities and 5,373,143 review records
- Review dates: 2008-11-16 through 2021-03-01

Only `Listings.csv` is uploaded to the development data lake because the implemented market summaries do not use review records. The raw object remains private and encrypted. Glue writes a selected, cleaned subset to `processed/listings/` as city-partitioned Parquet; raw and processed data remain excluded from Git.

## Local files

Extract the source archive outside Git or into the ignored `data/raw/` directory so these paths exist:

| File | Description | Rows | SHA-256 |
|------|-------------|-----:|---------|
| `data/raw/Airbnb Data/Listings.csv` | Listing attributes and nightly price in each city's local currency | 279,712 | `097b0bbfea3cce3cd9af7a717408c1027ca7f6dc947b7f27988a5c08085667db` |
| `data/raw/Airbnb Data/Reviews.csv` | Review identifiers and dates, without review text | 5,373,143 | `f0163d09e65bd9c88bec899eba77edd07101cf05b7aac2d2b0d745320e1d8e3f` |

## Observed quality limitations

- `Listings.csv` contains invalid UTF-8 byte sequences. Profiling uses UTF-8 replacement decoding and records 984 replacement characters.
- Price is highly right-skewed. There are 113 non-positive values and a maximum of 625,216.
- Prices use different local currencies across cities, so pooled currency-error metrics are not directly meaningful.
- `review_scores_rating` is missing for 32.7% of listings.
- `bedrooms` is missing for 10.5% of listings.
- `district` is missing for 86.8% of listings.
- Reviews contains no review text, so sentiment analysis is unsupported.

The complete generated profile is stored at `analytics/artifacts/data_profile.json`. See `DATA_DICTIONARY.md` for field definitions.
