LABS = [
    {
        "id": "latency-spike",
        "name": "Latency Spike",
        "status": "idle",
        "problem_statement": (
            "P99 response times have jumped from 120ms to over 2s. Users are reporting "
            "timeouts on checkout. No deployments have occurred in the last 6 hours."
        ),
    },
    {
        "id": "memory-leak",
        "name": "Memory Leak",
        "status": "idle",
        "problem_statement": (
            "Memory usage on api-worker pods is climbing steadily with flat traffic. "
            "OOM kills started 20 minutes ago and Kubernetes is thrashing restarts."
        ),
    },
    {
        "id": "cascade-failure",
        "name": "Cascade Failure",
        "status": "idle",
        "problem_statement": (
            "The auth service went offline and downstream services are failing open. "
            "Error rate is at 34% and climbing as retries amplify load across the mesh."
        ),
    },
]


def get_lab(lab_id: str) -> dict | None:
    return next((lab for lab in LABS if lab["id"] == lab_id), None)
