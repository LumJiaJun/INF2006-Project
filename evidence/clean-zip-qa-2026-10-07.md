# Clean-ZIP QA Record - 2026-10-07

Suggested reviewer: Leow Yi Hao Ignatius (2501538), with support from the team.

## Preparation completed

Nixon Lee Disheng ran the automated checks below on 2026-10-07 with Claude Code
assistance. This provides a working baseline for another teammate to verify
independently. Ignatius can repeat the checks on his own machine, record any
differences, and add his sign-off so the team has an independent QA review.

## Automated preparation

1. `git archive --format=zip HEAD` produced a 2.1 MB ZIP.
2. Extracted: `README.md`, `project_manifest.yaml`, `AI_USE_DECLARATION.md`, `TEAM_CONTRIBUTIONS.md`, `report.md`, `report.pdf`, `src/`, `data/`, `analytics/`, `tests/`, `evidence/`, `video_link.txt` sit at the ZIP root.
3. No `*.tfstate*`, `*.tfplan`, `.env`, `backend.hcl`, `*.joblib`, `Listings.csv`, or `tmp/` in the archive.
4. Every relative path in `project_manifest.yaml` exists in the extracted copy.
5. `python tests/local_preflight.py --include-ml` completed successfully from the extracted copy.

## Suggested independent review

Using the live site URL shared by Nixon, work through the checks below and note
anything that behaves differently from the expected result:

- [ ] Open the site signed out. Run a quick-profile estimate for Bangkok and for Paris. Record the displayed price and currency.
- [ ] Open Markets, select Paris, and confirm the median matches the chatbot answer (EUR 80.18) and the table.
- [ ] If practical, create a test account with email verification and TOTP, sign in, run an estimate, and confirm it appears under Recent predictions.
- [ ] Ask the guide "give me median paris" and "which city has the most listings" (expected: Paris, 64,020).
- [ ] Open Project; confirm the architecture claims match the README.
- [ ] Note any broken link, wrong number, or unclear wording.

## Independent review notes

- Reviewer: Leow Yi Hao Ignatius (2501538)
- Date and environment: 9 October 2026, clean Windows reproduction.
- Checks completed: Clean repository reproduction, report comparison, and
  targeted functional and validation probes.
- Findings or suggestions: The prioritised findings were validated and resolved
  as recorded in `sanity-review-fixes-2026-10-09.md`.
- Confirmation: The team confirmed this review for the final contribution
  summary on 10 October 2026.
