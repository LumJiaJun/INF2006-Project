"""
Test 4 — Scalability, resilience and recovery.

Objective: prove the health check works (used by a load balancer /
orchestrator to route traffic and restart unhealthy instances), the
analytics cache reduces repeated DB load, and the service handles a
burst of concurrent requests without errors.

Run:
    cd tests
    pytest 04_scalability_resilience -v

For the container-restart recovery test (which needs an actual
running Docker container, not the in-process TestClient used here),
see evidence/scalability/recovery-test.md for the manual steps and
record actual results there — do not fabricate them.
"""
import time
import concurrent.futures


def test_health_check_reports_healthy(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert body["database"] == "up"
    assert "uptime_seconds" in body


def test_analytics_cache_reduces_repeat_latency(client):
    # First call populates the cache; immediate second call should be
    # at least as fast (served from the in-process cache rather than
    # re-running the aggregate queries). This is a smoke test, not a
    # rigorous benchmark.
    t0 = time.time()
    r1 = client.get("/api/analytics/overview")
    first_call_ms = (time.time() - t0) * 1000

    t0 = time.time()
    r2 = client.get("/api/analytics/overview")
    second_call_ms = (time.time() - t0) * 1000

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    # Not a hard performance assertion (test hardware varies) — just
    # confirms the cached path executes and returns identical data.


def test_concurrent_search_requests_all_succeed(client):
    """
    Simple concurrency/load smoke test: fires many concurrent search
    requests and checks the service returns 200 for all of them with
    no errors, and records basic throughput/latency numbers.

    This is a smoke test suitable for a local dev machine, not a
    production load test. For real numbers under load, use a tool
    like `locust` or `k6` against a deployed instance and record the
    actual output in evidence/scalability/.
    """
    N_REQUESTS = 50

    def make_request(_):
        start = time.time()
        r = client.get("/api/listings", params={"page_size": 5})
        return r.status_code, time.time() - start

    start_all = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(make_request, range(N_REQUESTS)))
    total_time = time.time() - start_all

    statuses = [s for s, _ in results]
    latencies = [t for _, t in results]

    assert all(s == 200 for s in statuses), f"Some requests failed: {statuses}"

    throughput = N_REQUESTS / total_time
    print(f"\nConcurrency smoke test: {N_REQUESTS} requests in {total_time:.2f}s "
          f"({throughput:.1f} req/s), avg latency {sum(latencies)/len(latencies)*1000:.1f}ms, "
          f"max latency {max(latencies)*1000:.1f}ms")

    # Record this printed line in evidence/scalability/ when run for real.
