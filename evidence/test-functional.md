# Test 1 — Functional Workflow Test

**Objective:** prove the core guest workflow works end to end: register → login →
search → view listing → select dates → book → booking appears in My Trips.

**Setup:** local dev environment, Python 3.12, SQLite test database
(isolated from the dev database, created fresh per test run by
`tests/conftest.py`), backend started via FastAPI TestClient
(no separate server process needed for this automated run).

**Command:**
```
cd tests
pytest 01_functional -v
```

**Test cases and results:**

| Test | Expected result | Actual result |
|---|---|---|
| `test_register_login_search_book_workflow` | Full workflow (register→login→search→view→book→my trips) succeeds, booking appears in My Trips | PASS |
| `test_booking_rejects_invalid_dates` | check_out before check_in rejected with 422 | PASS |
| `test_double_booking_is_rejected` | Second overlapping booking on the same listing rejected with 409 | PASS |
| `test_recommendations_respect_budget_and_capacity` | Budget/guest-based recommendations return listings matching capacity, each with a fair-price estimate and match reason | PASS |
| `test_recommendations_rejects_invalid_budget_range` | budget_min > budget_max rejected with 422 | PASS |

**Actual output (captured 2026-09-22, see `evidence/pytest-output.txt` for the full 26-test run):**
```
01_functional/test_functional.py::test_register_login_search_book_workflow PASSED
01_functional/test_functional.py::test_booking_rejects_invalid_dates PASSED
01_functional/test_functional.py::test_double_booking_is_rejected PASSED
01_functional/test_functional.py::test_recommendations_respect_budget_and_capacity PASSED
01_functional/test_functional.py::test_recommendations_rejects_invalid_budget_range PASSED
5 passed
```

**Manual end-to-end confirmation (real HTTP server, not TestClient):**
Register → login → search (`city=Singapore`) → view listing detail → book
(`listing_id=270`, 2026-11-01 to 2026-11-05, 4 guests) → booking appeared in
`GET /api/bookings`. A second overlapping booking attempt correctly returned
`409 Listing is not available for the selected dates`.

Separately re-verified on 2026-09-22 via the "Find your match" flow: called
`/api/recommendations` (budget $50-200, 2 guests, Singapore), booked the
top-ranked listing (`listing_id=147`, 4 nights), and confirmed the booking
appeared correctly in `GET /api/bookings` with the right total ($323.68).

**Date:** 2026-09-21
**Artefact path:** `evidence/test-functional.md` (this file),
raw pytest log at `evidence/pytest-output.txt`

**Limitations:** Run so far only against the synthetic/dummy dataset and on a
local machine, not the deployed cloud instance. Once deployed, re-run against
the live URL and append results below with date and outcome.

**NOT YET EXECUTED:** end-to-end test against the deployed AWS instance.
