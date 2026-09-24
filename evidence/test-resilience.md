# Test 4 — Scalability, Resilience and Recovery Test

**Objective:** prove the health check mechanism works (used by a load
balancer/orchestrator to route traffic and restart unhealthy instances),
the analytics caching mechanism functions, and the service handles a burst
of concurrent requests without errors.

**Mechanism implemented:** `/api/health` endpoint (checks DB connectivity),
stateless JWT auth (no server-side session, so any instance can serve any
request — required for horizontal scaling), connection pooling
(`pool_pre_ping`, `pool_size=5`, `max_overflow=10`), and a 30-second
in-process TTL cache on `/api/analytics/overview` to reduce repeated
aggregate-query load. See `docs/ARCHITECTURE.md` for how these fit into
the target AWS deployment (ALB health checks + multiple app instances).

**Command:**
```
cd tests
pytest 04_scalability_resilience -v
```

**Test cases and results:**

| Test | Expected result | Actual result |
|---|---|---|
| `test_health_check_reports_healthy` | `/api/health` returns `status: healthy`, `database: up` | PASS |
| `test_analytics_cache_reduces_repeat_latency` | Second call to analytics returns identical cached data | PASS |
| `test_concurrent_search_requests_all_succeed` | 50 concurrent search requests (10 workers) all return 200 | PASS |

**Actual output (captured 2026-09-21 09:48:14 UTC):**
```
04_scalability_resilience/test_resilience.py::test_health_check_reports_healthy PASSED
04_scalability_resilience/test_resilience.py::test_analytics_cache_reduces_repeat_latency PASSED
04_scalability_resilience/test_resilience.py::test_concurrent_search_requests_all_succeed PASSED
3 passed
```

**Concurrency smoke test measured numbers:** run against the FastAPI
TestClient (in-process, not a real network hop), 50 requests / 10 workers —
all 50 returned HTTP 200. Printed throughput/latency line is captured in
`evidence/pytest-output.txt` when run with `pytest -s`. This is
a smoke test only; it does not represent real network latency or a
production load profile.

## Recovery test (manual — requires a running Docker container)

**NOT YET EXECUTED.** Procedure to run once deployed (locally via Docker
Compose, or on AWS):

1. `docker compose up -d` and confirm `curl localhost:8000/api/health`
   returns `status: healthy`.
2. `docker compose stop backend` to simulate a component failure.
3. Confirm the health check fails (connection refused / non-200), which is
   what a load balancer would detect to stop routing traffic.
4. `docker compose start backend`.
5. Confirm `/api/health` returns healthy again and that a booking made
   before the restart is still visible in `GET /api/bookings` (proves the
   Postgres data volume persisted independently of the backend container).
6. Record the actual timestamps and outputs of each step here.

**Date:** 2026-09-21 (automated tests only; recovery test pending an
actual Docker/AWS environment)
**Artefact path:** `evidence/test-resilience.md` (this file)

**Limitations:** No real production-scale load test (e.g. locust/k6) has
been run yet, and no real container restart has been performed. These
require a running Docker or AWS environment that hasn't been set up. Marked
honestly as NOT YET EXECUTED rather than fabricated.
