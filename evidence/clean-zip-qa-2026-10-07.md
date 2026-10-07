# Clean-ZIP QA Record - 2026-10-07

Role: Application QA reviewer (Leow Yi Hao Ignatius, 2501538).

## Status

The automated steps below were executed on 2026-10-07 by Nixon Lee Disheng with
Claude Code assistance, on Nixon's machine, as a preparation for the QA role.
They were NOT run by Ignatius. Ignatius must repeat them on his own machine and
complete the sign-off section before this file is presented as his work.

## Automated steps run (by Nixon with Claude Code)

1. `git archive --format=zip HEAD` produced a 2.1 MB ZIP.
2. Extracted: `README.md`, `project_manifest.yaml`, `AI_USE_DECLARATION.md`, `TEAM_CONTRIBUTIONS.md`, `report.md`, `report.pdf`, `src/`, `data/`, `analytics/`, `tests/`, `evidence/`, `video_link.txt` sit at the ZIP root.
3. No `*.tfstate*`, `*.tfplan`, `.env`, `backend.hcl`, `*.joblib`, `Listings.csv`, or `tmp/` in the archive.
4. Every relative path in `project_manifest.yaml` exists in the extracted copy.
5. `python tests/local_preflight.py --include-ml` completed successfully from the extracted copy.

## Manual journey for Ignatius to run and record

Against the live site (URL from `terraform output frontend_url`, or ask Nixon):

- [ ] Open the site signed out. Run a quick-profile estimate for Bangkok and for Paris. Record the displayed price and currency.
- [ ] Open Markets, select Paris, and confirm the median matches the chatbot answer (EUR 80.18) and the table.
- [ ] Sign up (email verification and TOTP), sign in, run an estimate, and confirm it appears under Recent predictions.
- [ ] Ask the guide "give me median paris" and "which city has the most listings" (expected: Paris, 64,020).
- [ ] Open Project; confirm the architecture claims match the README.
- [ ] Note any broken link, wrong number, or unclear wording.

## Sign-off (to be completed by Ignatius)

- Date and machine:
- Steps repeated:
- Findings:
- Commit that adds this completed record:
