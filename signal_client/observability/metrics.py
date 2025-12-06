"""Prometheus metrics definitions for the Signal client."""

from __future__ import annotations

from prometheus_client import (
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)
from prometheus_client.exposition import generate_latest

WEBSOCKET_EVENTS = Counter(
    "websocket_events_total",
    "Websocket lifecycle events",
    labelnames=("event",),
)
WEBSOCKET_CONNECTION_STATE = Gauge(
    "websocket_connection_state",
    "Current websocket connection state (1=connected, 0=disconnected)",
)
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
DLQ_EVENTS = Counter(
    "dlq_events_total",
    "DLQ enqueue/replay results",
    labelnames=("queue", "event"),
)
INGEST_PAUSES = Counter(
    "ingest_pauses_total",
    "Number of times ingest was paused due to backpressure or circuit conditions",
    labelnames=("reason",),
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
COMMANDS_PROCESSED = Counter(
    "command_calls_total",
    "Command handler outcomes",
    labelnames=("command", "status"),
)
COMMAND_LATENCY = Histogram(
    "command_latency_seconds",
    "Command handler latency",
    labelnames=("command", "status"),
)
SHARD_QUEUE_DEPTH = Gauge(
    "message_shard_queue_depth",
    "Current depth of each shard queue",
    labelnames=("shard",),
)


def render_metrics(registry: CollectorRegistry | None = None) -> bytes:
    """Render all registered metrics as Prometheus exposition format."""
    return generate_latest(registry or REGISTRY)


def start_metrics_server(
    port: int = 8000,
    addr: str = "127.0.0.1",
    *,
    registry: CollectorRegistry | None = None,
) -> object:
    """Start an HTTP server that exposes Prometheus metrics at `/`.

    Returns the server object so callers can stop it if desired.
    """
    return start_http_server(port, addr=addr, registry=registry or REGISTRY)
