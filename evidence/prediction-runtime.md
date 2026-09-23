# Prediction runtime packaging evidence

- **Objective:** Package the complete preprocessing and model pipeline for Lambda while preserving dependency compatibility and secure image handling.
- **Measured dependency size:** Approximately 257.66 MB for scikit-learn, NumPy, SciPy, pandas, joblib, and threadpool support before adding the model and metadata.
- **Decision:** Use a Lambda container image because the measured dependencies exceed the 250 MB unzipped ZIP and layer limit documented in the [AWS Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).
- **Compatibility finding:** scikit-learn 1.9.1 and SciPy 1.17.1 did not provide compatible manylinux wheels for the Lambda Python 3.11 base. Training and inference were aligned on scikit-learn 1.7.2 and SciPy 1.15.3.
- **Build command:** `docker build --platform linux/amd64 --provenance=false -f src/backend/predict/Dockerfile -t airbnb-prediction:1.0.2 .`
- **Local functional result:** The Lambda runtime interface returned HTTP 200 with a real model estimate of 65.98 EUR for a valid Paris input and HTTP 400 with code `invalid_json` for malformed JSON.
- **Registry controls:** Terraform created an encrypted ECR repository with immutable tags, scan-on-push, and a three-image lifecycle policy.
- **Published image:** Tag `1.0.2`, Docker V2 single-architecture manifest. It disables unused joblib multiprocessing to avoid restricted shared-memory warnings in Lambda.
- **Deployed latency:** The first 1 GB invocation measured 13.8 seconds and warm requests measured 59 to 70 ms. After increasing Lambda memory to 2 GB, fresh-environment requests measured approximately 3.0 to 3.3 seconds.
- **Image scan:** Completed successfully with no severity findings reported on 2026-09-23.
- **Limitation:** A clean scan does not prove the image has no vulnerability or application-level security flaw.
- **Date:** 2026-09-23
- **Artefact paths:** `src/backend/predict/Dockerfile`, `src/backend/predict/handler.py`, `analytics/requirements-inference.txt`, and `src/infrastructure/ecr.tf`
