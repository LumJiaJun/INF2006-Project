# Cloud data pipeline evidence

- **Objective:** Convert the raw listings CSV into an analytics-optimized format and query it through managed serverless services.
- **Setup:** Private encrypted S3 data lake, AWS Glue 5.0 Spark job, Glue Data Catalog table with city partition projection, and a governed Athena workgroup.
- **Command / steps:** Upload `Listings.csv` to `raw/listings/`, run `aws glue start-job-run --job-name airbnb-market-intelligence-dev-listings-transform`, inspect `processed/listings/`, then invoke `GET /analytics`.
- **Expected result:** Glue succeeds, writes one or more Parquet objects for all ten observed cities, and the fixed Athena query returns a ten-city summary.
- **Actual result:** Passed on 2026-09-23. Glue run `jr_3a0acfe750c7f8bcf8d975e51a7f188948f3890f6e8f87a606bc531c80496a48` succeeded in 90 seconds. The 158,497,169-byte raw CSV produced ten city-partitioned Parquet objects totalling 1,223,651 bytes. This size comparison is descriptive and does not isolate compression from column selection and row filtering.
- **Athena result:** A live city-summary query returned ten cities, scanned 566,077 bytes, used 574 ms of engine time, and completed in 697 ms. The API request completed in approximately 1.3 seconds during the recorded test.
- **Interpretation:** Parquet and projection keep this approved aggregate query small. These observations apply to this dataset and query only and are not a general performance benchmark.
- **Artefact path:** `analytics/glue_transform.py`, `src/infrastructure/data_lake.tf`, `src/backend/analytics/handler.py`, and `tests/test_analytics.py`
