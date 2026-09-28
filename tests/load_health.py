import argparse
import concurrent.futures
import ipaddress
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request


def request(url):
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
    elapsed_ms = (time.perf_counter() - started) * 1000
    return status, elapsed_ms


def main():
    parser = argparse.ArgumentParser(description="Run a bounded concurrent health-endpoint check.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--allowed-host")
    parser.add_argument("--confirm-authorized-target", action="store_true")
    args = parser.parse_args()

    if not 1 <= args.requests <= 100:
        parser.error("--requests must be between 1 and 100")
    if not 1 <= args.concurrency <= 10:
        parser.error("--concurrency must be between 1 and 10")

    parsed_url = urllib.parse.urlparse(args.url)
    if not parsed_url.hostname or parsed_url.scheme not in {"http", "https"}:
        parser.error("--url must be an absolute HTTP or HTTPS URL")

    try:
        loopback = ipaddress.ip_address(parsed_url.hostname).is_loopback
    except ValueError:
        loopback = parsed_url.hostname.lower() == "localhost"

    if not loopback:
        if parsed_url.scheme != "https":
            parser.error("non-loopback load-test targets must use HTTPS")
        if not args.confirm_authorized_target:
            parser.error("use --confirm-authorized-target only for a target you are authorized to test")
        if args.allowed_host != parsed_url.hostname:
            parser.error("--allowed-host must exactly match the target hostname")

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(request, [args.url] * args.requests))
    total_seconds = time.perf_counter() - started

    statuses = {}
    durations = []
    for status, elapsed_ms in results:
        statuses[status] = statuses.get(status, 0) + 1
        durations.append(elapsed_ms)

    output = {
        "requests": args.requests,
        "concurrency": args.concurrency,
        "status_counts": statuses,
        "elapsed_seconds": round(total_seconds, 3),
        "requests_per_second": round(args.requests / total_seconds, 2),
        "latency_ms": {
            "minimum": round(min(durations), 2),
            "median": round(statistics.median(durations), 2),
            "maximum": round(max(durations), 2),
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))

    unexpected = set(statuses) - {200, 429}
    # Controlled throttling is acceptable, but backend failures make the check fail.
    if unexpected or statuses.get(200, 0) == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
