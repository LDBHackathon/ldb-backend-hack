from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    name="ldb_dva_http_requests_total",
    documentation="Total HTTP requests",
    labelnames=["method", "path", "status_code"],
)

http_request_duration = Histogram(
    name="ldb_dva_http_request_duration_seconds",
    documentation="HTTP request duration in seconds",
    labelnames=["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)
