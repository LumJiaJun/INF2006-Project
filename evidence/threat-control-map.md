# Threat-Control Map

Concise version for the manifest/evidence trail. Full detail (attack
scenario, implementation file, test, evidence) for each item is in
`docs/THREAT_MODEL.md`.

| # | Threat | Control | Implementation | Test | Status |
|---|---|---|---|---|---|
| 1 | SQL injection | Parameterized ORM queries (SQLAlchemy), no raw SQL string concatenation | `src/backend/app/routers/listings.py`, `bookings.py` | `test_sql_injection_payload_is_not_executed` | PASS |
| 2 | Unauthorized API access | JWT bearer auth required on protected routes | `src/backend/app/auth.py` | `test_unauthenticated_booking_rejected`, `test_invalid_jwt_rejected` | PASS |
| 3 | Privilege escalation / broken object-level and role-based authorization | Server-side ownership checks on bookings; `require_role("admin")` dependency guards all `/api/admin/*` routes | `src/backend/app/routers/bookings.py`, `routers/admin.py`, `auth.py` | `test_guest_cannot_cancel_another_users_booking`, `test_guest_cannot_access_admin_analytics`, `test_guest_cannot_create_listing_via_admin_endpoint`, `test_admin_can_manage_listings` | PASS |
| 4 | Credential leakage via plaintext passwords | bcrypt password hashing | `src/backend/app/auth.py` | `test_password_not_stored_in_plaintext` | PASS |
| 5 | Malicious/malformed input | Pydantic schema validation, typed fields, custom validators | `src/backend/app/schemas.py` | `test_malformed_registration_rejected`, `test_booking_rejects_invalid_dates` | PASS |
| 6 | Unauthorized database access (network) | RDS security group restricted to backend SG only, no public accessibility | AWS RDS config (`docs/DEPLOYMENT.md` Step 3) | Manual verification post-deployment | NOT YET EXECUTED (no AWS deployment yet) |
| 7 | Insecure secrets handling | Env-var-based secrets, `.env` git-ignored, AWS Secrets Manager planned for deployment | `src/backend/app/auth.py`, `database.py`, `.env.example` | Code review (no hardcoded secrets found) | PASS (app-level); Secrets Manager wiring MANUAL USER ACTION REQUIRED |
| 8 | Sensitive information exposure through logs | Logging middleware logs only method/path/status/duration, never body/password/token | `src/backend/app/main.py`, `routers/auth_routes.py` | Manual code review (`grep` for password/token in logger calls returns none) | PASS |

**Date:** 2026-09-21
**Full detail:** `docs/THREAT_MODEL.md`
**Test output backing the PASS rows:** `evidence/test-security.md`, `evidence/pytest-output.txt`
