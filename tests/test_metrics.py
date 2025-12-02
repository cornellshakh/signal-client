from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter

from signal_client.observability.metrics import (
    API_CLIENT_PERFORMANCE,
    CIRCUIT_BREAKER_STATE,
    DLQ_BACKLOG,
    ERRORS_OCCURRED,
    MESSAGE_QUEUE_DEPTH,
    MESSAGE_QUEUE_LATENCY,
    MESSAGES_PROCESSED,
    RATE_LIMITER_WAIT,
    render_metrics,
)


def test_render_metrics_supports_custom_registry():
    registry = CollectorRegistry()
    counter = Counter("custom_counter", "help", registry=registry)  # type: ignore[name-defined]
    counter.inc()

    output = render_metrics(registry)
    assert "custom_counter" in output.decode("utf-8")


def test_render_metrics_uses_default_registry():
    MESSAGES_PROCESSED.inc()
    ERRORS_OCCURRED.inc()
    with API_CLIENT_PERFORMANCE.time():
        pass

    output = render_metrics()
    text = output.decode("utf-8")
    assert "messages_processed_total" in text
    assert "errors_occurred_total" in text


def test_new_metrics_can_be_recorded():
    MESSAGE_QUEUE_DEPTH.set(5)
    MESSAGE_QUEUE_LATENCY.observe(0.05)
    DLQ_BACKLOG.labels(queue="signal_client_dlq").set(2)
    RATE_LIMITER_WAIT.observe(0.01)
    CIRCUIT_BREAKER_STATE.labels(endpoint="/messages", state="closed").set(1)

    output = render_metrics()
    text = output.decode("utf-8")
    assert "message_queue_depth" in text
    assert "message_queue_latency_seconds_bucket" in text
    assert "dead_letter_queue_depth" in text
    assert "rate_limiter_wait_seconds_bucket" in text
    assert "circuit_breaker_state" in text
