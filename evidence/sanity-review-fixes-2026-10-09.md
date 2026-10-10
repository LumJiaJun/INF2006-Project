# Sanity Review Fixes and Live Recheck - 2026-10-09

Redacted: no account IDs, tokens, or personal data. Region ap-southeast-1.

An independent teammate-run review on 2026-10-09 (clean Windows reproduction,
report comparison, targeted probes) reported five blocking items. Each was
validated against the code before changing anything.

## Findings validated and fixed

| Finding | Validated how | Fix | Verification |
|---------|---------------|-----|--------------|
| F1 CSV byte hash fails on Windows archives | `git archive` under `core.autocrlf=true` produced 501 CRLF lines and SHA-256 `9360b2cf...`; the generator emits LF with SHA-256 `36e4bfe1...`. Index and working copies were LF. | `.gitattributes`: `*.csv text eol=lf`. No data or test change. | Same archive command now gives 0 CRLF lines and `36e4bfe1...`. Full unit suite (53 tests) and `local_preflight.py --include-ml` pass from an extract of that archive. |
| F2 Saved-prediction retry fails after a partial write | Read `src/backend/predict/handler.py`: random history ID, no recovery from a stalled `IN_PROGRESS` record, eventually consistent read, no `expires_at` check. | History ID and timestamp are fixed at claim time from a hash of user and key. A 60 second lease lets a retry take over a stalled attempt. The history write tolerates "already exists". Reads are consistent. Records past `expires_at` are replaced atomically. The frontend reuses the key when the identical form is resubmitted after a failure. | 5 new unit tests (history write failure, completion failure, active lease, changed input, expired record) fail on the old handler and pass on the new one. Live check below. |
| F3 Chat crashes on non-string `page` | Read `parse_request`: set membership on a list raises `TypeError`. | `isinstance(page, str)` before membership. | New test over `[]`, `{}`, `None`, `7`, `True`, `["index.html"]` fails without the fix and passes with it; no model call is made. Live check below. |
| F4 Report inaccuracies | Compared `report.md` with `analytics/train_model.py`, the chat handler, Terraform and evidence. | Corrected the baseline (global median, `DummyRegressor(strategy="median")`), disclosed that candidate selection and reported metrics share one held-out split, explained that Glue's analytics boundary is computed separately from the model's training-only thresholds, updated the chat token cap (300), bucket retention wording, Bedrock global-profile region wording, deploy-gate wording, DAST wording, and test counts (53). | Text review. The supplied Word report and `report.pdf` are separate artefacts and were not regenerated here. |
| F5 Contribution and QA sign-off | Read `TEAM_CONTRIBUTIONS.md` and `clean-zip-qa-2026-10-07.md`. | Initially left open because it required team confirmation. The team confirmed Ignatius's review and the final contribution summary on 10 October 2026. | Resolved after team confirmation. |

## Deployment

- Built the prediction image from `analytics/artifacts/airbnb_price_model.joblib`
  whose SHA-256 matches `model_artifact.sha256` in `model_evaluation.json`
  (`e6d12bc0...`). The model loads inside the built image (version 1.0.0).
- Pushed as ECR tag `fix-aa4fdcf` (immutable tag, digest `sha256:5bf865ef...`).
- Reviewed saved plan: 3 in-place changes (chat Lambda code, prediction image
  tag, `app.js` object). Applied it. A following plan reported no changes.
- Rollback tag from the previous deployment: `d7fb1bdd1c61`.
- When planning against this stack pass `-var="prediction_image_tag=fix-libxml2"`
  and the alert email variable; the default image tag variable is stale (see the image findings section for the current live tag).

## Live checks (direct Lambda invocation, synthetic user, records deleted afterwards)

Script: `tests/verify_live_recovery.py --i-confirm-authorized-target`.

| Check | Result |
|-------|--------|
| Save with a key | HTTP 200, saved true |
| Replay the same key | HTTP 200, same prediction ID |
| Same key, changed input | HTTP 409 `idempotency_conflict` |
| New key, same input | HTTP 200, new prediction ID (a new submission) |
| History rows for the synthetic user | 2 (one per distinct key) |
| Chat with `page` = `[]`, `{}`, `null`, `7` | HTTP 400 `invalid_request` each |
| Cleanup | 0 history rows and 0 idempotency records left |

Public smoke (`tests/smoke_api.ps1`) passed after deployment. The live `app.js`
contains the key-reuse code.

## Not verified here

- The stalled-attempt lease takeover and completion-failure recovery were
  verified by unit tests with injected failures, not by forcing a DynamoDB
  failure on the deployed stack.
- A real signed-in browser retry after an injected failure.
- Word report, `report.pdf`, final ZIP, and the contribution sign-offs.

## Report PDF rebuild (2026-10-09)

`report.pdf` was regenerated from `report.md` because the earlier PDF was stale
(46 tests, 220 tokens, pending SNS). Recipe used: `pandoc` (bundled with Quarto
1.8) converts `report.md` to standalone HTML with the architecture figure
inserted before section 3 on its own landscape page and a print stylesheet, then
headless Chrome prints it to A4. Result: 10 pages, figure legible. The supplied
Word report is a separate artefact and still needs the same corrections applied
by its owner. The PDF contains the facts in `report.md` as of this commit; it
must be rebuilt if `report.md` changes again.

## Image vulnerability findings (2026-10-09)

The prediction image `fix-aa4fdcf` scanned at 0 CRITICAL, 0 HIGH, 6 MEDIUM and
1 LOW findings, all in the base image's `libxml2` 2.9.1 (CVE-2026-74860,
CVE-2026-86137 to CVE-2026-86144 range). The handler parses JSON only and the
image does not install `lxml`, so the exposure was low, but a patched package
(`2.9.1-6.amzn2.5.27`) was available. The Dockerfile now runs
`yum update -y curl libcurl libxml2`. Rebuilt image `fix-libxml2` (digest
`sha256:081bd5d0...`) scanned with no findings. It loads the model (version
1.0.0), was deployed with a reviewed one-resource saved plan, and the live
checks above were repeated and passed. A following plan showed no drift. The
live image tag is now `fix-libxml2`; rollback tags are `fix-aa4fdcf` and
`d7fb1bdd1c61`. A clean scan is a point-in-time result: new CVEs can appear
against the same image later, so this is not a zero-vulnerability claim.
