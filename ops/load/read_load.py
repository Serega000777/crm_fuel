"""Read-only HTTP load probe for a deployed CRM Fuel API."""

import concurrent.futures
import os
import statistics
import time
import urllib.error
import urllib.request


def request_once(url: str, authorization: str) -> tuple[float, int]:
    headers = {"Authorization": authorization} if authorization else {"X-Dev-User": "1"}
    request = urllib.request.Request(f"{url}/api/v1/fuels", headers=headers)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
            return time.perf_counter() - started, response.status
    except (urllib.error.URLError, TimeoutError):
        return time.perf_counter() - started, 0


def main() -> None:
    base_url = os.environ["BASE_URL"].rstrip("/")
    authorization = os.environ.get("AUTHORIZATION", "")
    total = int(os.environ.get("TOTAL_REQUESTS", "5000"))
    concurrency = int(os.environ.get("CONCURRENCY", "50"))
    max_error_rate = float(os.environ.get("MAX_ERROR_RATE", "0.01"))
    max_p95_ms = float(os.environ.get("MAX_P95_MS", "1000"))
    if total < 1 or concurrency < 1 or concurrency > 500:
        raise RuntimeError("Invalid load parameters")

    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(
            pool.map(
                lambda _: request_once(base_url, authorization),
                range(total),
            )
        )
    elapsed = time.perf_counter() - started
    durations = sorted(duration * 1000 for duration, _ in results)
    errors = sum(status != 200 for _, status in results)
    error_rate = errors / total
    p95_index = max(0, min(total - 1, int(total * 0.95) - 1))
    p95_ms = durations[p95_index]
    print(
        f"requests={total} concurrency={concurrency} rps={total / elapsed:.1f} "
        f"mean_ms={statistics.mean(durations):.1f} p95_ms={p95_ms:.1f} "
        f"errors={errors} error_rate={error_rate:.4f}"
    )
    if error_rate > max_error_rate:
        raise RuntimeError("Error rate threshold exceeded")
    if p95_ms > max_p95_ms:
        raise RuntimeError("P95 latency threshold exceeded")


if __name__ == "__main__":
    main()
