from __future__ import annotations

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, Histogram
from prometheus_client.exposition import generate_latest

MESSAGES_PROCESSED = Counter(
    "messages_processed_total",
    "Total number of messages processed",
)
ERRORS_OCCURRED = Counter("errors_occurred_total", "Total number of errors occurred")
API_CLIENT_PERFORMANCE = Histogram(
    "api_client_performance_seconds", "API client request latency in seconds"
)
MESSAGE_QUEUE_DEPTH = Gauge(
    "message_queue_depth",
    "Current depth of the primary message queue",
)
MESSAGE_QUEUE_LATENCY = Histogram(
    "message_queue_latency_seconds",
    "Time spent by messages waiting in the queue before being processed",
)
DLQ_BACKLOG = Gauge(
    "dead_letter_queue_depth",
    "Number of messages currently held in the dead letter queue",
    labelnames=("queue",),
)
RATE_LIMITER_WAIT = Histogram(
    "rate_limiter_wait_seconds",
    "Amount of time spent waiting for rate limiter permits",
)
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "State of the circuit breaker per endpoint",
    labelnames=("endpoint", "state"),
)


def render_metrics(registry: CollectorRegistry | None = None) -> bytes:
    """Render all registered metrics as Prometheus exposition format."""
    return generate_latest(registry or REGISTRY)
