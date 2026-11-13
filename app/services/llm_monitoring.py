from collections import defaultdict

_metrics = defaultdict(
    lambda: {
        "requests": 0,
        "successes": 0,
        "failures": 0,
        "total_latency_ms": 0.0
    }
)

def record_request(
    provider: str,
    success: bool,
    latency_ms: float
):

    metric = _metrics[provider]

    metric["requests"] += 1

    if success:
        metric["successes"] += 1
    else:
        metric["failures"] += 1

    metric["total_latency_ms"] += latency_ms

def get_metrics():

    results = {}

    for provider, metric in _metrics.items():

        requests = metric["requests"]

        results[provider] = {
            **metric,
            "average_latency_ms": (
                metric["total_latency_ms"] / requests
                if requests else 0
            )
        }

    return results