# Threat Model — StaySphere

Scope: the web application and API described in this repository. Out of
scope: physical security, AWS account compromise at the console/IAM level
beyond what's documented below, and any real payment system (none exists —
all bookings are simulated).

## 1. SQL injection

- **Attack scenario:** an attacker submits a crafted string (e.g.
  `Singapore' OR '1'='1`) into a search filter, hoping the backend
  concatenates it into a raw SQL query and returns unauthorized data.
- **Control:** all database access goes through SQLAlchemy's ORM query
  builder, which parameterizes every value. No raw SQL string
  concatenation with user input exists anywhere in the codebase.
- **Implementation:** `src/backend/app/routers/listings.py`, `bookings.py`.
- **Test:** `tests/02_security/test_security.py::test_sql_injection_payload_is_not_executed`.
- **Evidence:** `evidence/test-security.md` — payload returned 0 rows instead of the full table.

## 2. Unauthorized API access

- **Attack scenario:** an unauthenticated client calls a protected
  endpoint (e.g. creating a booking, viewing another user's trips)
  directly against the API, bypassing the frontend.
- **Control:** protected routes depend on `auth.get_current_user`, which
  requires and validates a JWT bearer token before the route body runs.
- **Implementation:** `src/backend/app/auth.py`, used in `bookings.py`.
- **Test:** `test_unauthenticated_booking_rejected`, `test_invalid_jwt_rejected`.
- **Evidence:** `evidence/test-security.md`.

## 3. Privilege escalation / broken object-level authorization

- **Attack scenario:** a logged-in guest tries to cancel or view another
  user's booking by guessing/incrementing a booking ID.
- **Control:** `cancel_booking` explicitly checks `booking.guest_id ==
  current_user.user_id` (or admin role) before allowing the action.
  `my_trips` filters bookings by the authenticated user's ID server-side,
  never trusting a client-supplied user ID.
- **Implementation:** `src/backend/app/routers/bookings.py`.
- **Test:** `test_guest_cannot_cancel_another_users_booking`.
- **Evidence:** `evidence/test-security.md`.

## 4. Credential leakage via plaintext password storage

- **Attack scenario:** the database is exfiltrated (backup leak,
  misconfigured access) and passwords are recovered directly.
- **Control:** passwords are hashed with bcrypt (via `passlib`) before
  storage; the plaintext password is never persisted or logged.
- **Implementation:** `src/backend/app/auth.py` (`hash_password`).
- **Test:** `test_password_not_stored_in_plaintext`.
- **Evidence:** `evidence/test-security.md` — stored hash starts with `$2b$`.

## 5. Malicious / malformed input

- **Attack scenario:** a client sends invalid types, out-of-range
  numbers, or missing required fields to destabilize the app or bypass
  validation (e.g. negative guest counts, invalid email formats).
- **Control:** Pydantic schemas validate every request body (types,
  `EmailStr`, `Field(gt=0)` bounds, custom validators like
  `check_out_after_check_in`) before the route logic runs. FastAPI
  returns `422` automatically on validation failure.
- **Implementation:** `src/backend/app/schemas.py`.
- **Test:** `test_malformed_registration_rejected`, `test_booking_rejects_invalid_dates`, `test_price_estimate_rejects_invalid_input`.
- **Evidence:** `evidence/test-security.md`, `evidence/test-data-ai.md`.

## 6. Unauthorized database access (network-level)

- **Attack scenario:** the RDS instance is exposed to the public
  internet and an attacker connects directly, bypassing the API layer
  entirely.
- **Control (deployment-time, MANUAL USER ACTION REQUIRED):** the RDS
  security group must allow inbound traffic on port 5432 only from the
  backend's security group, never `0.0.0.0/0`. RDS must be placed in a
  private subnet with no public accessibility flag set. See
  `docs/DEPLOYMENT.md` for the exact manual steps.
- **Test:** cannot be automated from inside this repo (it's an AWS
  network configuration, not application code). **NOT YET EXECUTED** —
  to be verified manually once RDS is provisioned, by attempting to
  connect from outside the VPC and confirming the connection is refused.

## 7. Insecure secrets handling

- **Attack scenario:** JWT secret or database credentials are committed
  to source control or hardcoded, allowing anyone with repo access to
  forge tokens or connect directly to the database.
- **Control:** all secrets are read from environment variables
  (`JWT_SECRET`, `DATABASE_URL`), never hardcoded. `.env` is
  git-ignored; `.env.example` contains no real values. In AWS
  deployment, secrets should be stored in AWS Secrets Manager or
  Parameter Store and injected as environment variables at container
  startup, not baked into the image.
- **Implementation:** `src/backend/app/auth.py`, `database.py`, `.env.example`.
- **Status:** application-level control implemented. AWS Secrets
  Manager wiring is **MANUAL USER ACTION REQUIRED** (see `docs/DEPLOYMENT.md`)
  since it depends on the team's AWS account.

## 8. Sensitive information exposure through logs

- **Attack scenario:** passwords, tokens, or full request bodies get
  written to logs and later leaked via log access.
- **Control:** request logging middleware logs only method, path,
  status code and duration — never the request body, headers, or
  tokens. Auth logs record user IDs and email addresses on failure (for
  abuse monitoring) but never passwords.
- **Implementation:** `src/backend/app/main.py` (`log_requests`
  middleware), `routers/auth_routes.py`.
- **Test:** manual code review — no `password` or `token` variable is
  ever passed to a `logger.*()` call anywhere in the codebase (verified
  by grep as of 2026-09-21: `grep -rn "logger\." app/ | grep -i "password\|token"` returns no matches with actual secret values).

## Known gaps (not fabricated as solved)

- No rate limiting / brute-force lockout on `/api/auth/login` yet — a
  real gap for a public login endpoint. Would add `slowapi` or an
  API-gateway-level rate limit before any real deployment beyond this
  academic scope.
- No dependency vulnerability scanning (e.g. `pip-audit`) has been run yet.
- No WAF or DDoS protection configured (out of scope for project cost/complexity).
