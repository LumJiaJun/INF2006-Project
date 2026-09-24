# Test 2 — Security Control Test

**Objective:** prove authentication/authorization enforcement, rejection of
malformed and malicious input, and secure password storage.

**Threats tested (see `evidence/threat-control-map.md` / `docs/THREAT_MODEL.md`):**
unauthorized API access, privilege escalation, SQL injection, malicious/malformed
input, credential leakage via plaintext password storage.

**Setup:** same isolated SQLite test DB as Test 1, FastAPI TestClient.

**Command:**
```
cd tests
pytest 02_security -v
```

**Test cases and results:**

| Test | Threat | Expected result | Actual result |
|---|---|---|---|
| `test_unauthenticated_booking_rejected` | Unauthorized API access | 401 without a token | PASS |
| `test_invalid_jwt_rejected` | Forged/invalid credentials | 401 on a garbage bearer token | PASS |
| `test_wrong_password_rejected` | Credential brute force / leakage | 401 on wrong password, generic error message | PASS |
| `test_duplicate_registration_rejected` | Input validation | 400 on duplicate email | PASS |
| `test_malformed_registration_rejected` | Malicious/malformed input | 422 on invalid email + short password | PASS |
| `test_sql_injection_payload_is_not_executed` | SQL injection | Payload `Singapore' OR '1'='1` treated as a literal string, returns 0 rows, not the full table | PASS |
| `test_password_not_stored_in_plaintext` | Credential leakage | DB stores a bcrypt hash (`$2b$...`), never the plaintext password | PASS |
| `test_guest_cannot_cancel_another_users_booking` | Privilege escalation / broken object-level authorization | User B gets 403 trying to cancel User A's booking | PASS |
| `test_guest_cannot_access_admin_analytics` | Privilege escalation (role) | Guest role gets 403 on admin-only analytics endpoint | PASS |
| `test_guest_cannot_create_listing_via_admin_endpoint` | Privilege escalation (role) | Guest role gets 403 creating a listing via the admin endpoint | PASS |
| `test_admin_can_manage_listings` | Role-based authorization (positive case) | An admin-role user can view admin analytics, create, update and delete a listing | PASS |
| `test_guest_cannot_access_admin_bookings_or_pricing_insights` | Privilege escalation (role) | Guest role gets 403 on `/api/admin/bookings`, `/api/admin/pricing-insights` and `/api/admin/listings-pricing` | PASS |

**Actual output (captured 2026-09-21 09:48:14 UTC):**
```
02_security/test_security.py::test_unauthenticated_booking_rejected PASSED
02_security/test_security.py::test_invalid_jwt_rejected PASSED
02_security/test_security.py::test_wrong_password_rejected PASSED
02_security/test_security.py::test_duplicate_registration_rejected PASSED
02_security/test_security.py::test_malformed_registration_rejected PASSED
02_security/test_security.py::test_sql_injection_payload_is_not_executed PASSED
02_security/test_security.py::test_password_not_stored_in_plaintext PASSED
02_security/test_security.py::test_guest_cannot_cancel_another_users_booking PASSED
02_security/test_security.py::test_guest_cannot_access_admin_analytics PASSED
02_security/test_security.py::test_guest_cannot_create_listing_via_admin_endpoint PASSED
02_security/test_security.py::test_admin_can_manage_listings PASSED
02_security/test_security.py::test_guest_cannot_access_admin_bookings_or_pricing_insights PASSED
12 passed
```

**Manual confirmation against a real running server:** also verified by hand
with curl against `localhost:8000` on 2026-09-21 — a SQL-injection-style city
filter (`Singapore' OR '1'='1`) returned `{"total": 0}` rather than every
listing, confirming the ORM's parameterized queries prevent injection.

**Date:** 2026-09-21
**Artefact path:** `evidence/test-security.md` (this file)

**Limitations:** No penetration test or automated dependency/vulnerability
scan has been run (e.g. `pip-audit`, `npm audit`, OWASP ZAP). No rate-limiting
or brute-force lockout is implemented yet, which is a real gap for a
public-facing login endpoint — documented as a limitation in
`docs/THREAT_MODEL.md`, not hidden.

**NOT YET EXECUTED:** dependency vulnerability scan; security test against the
deployed AWS instance including network/security-group configuration checks.
