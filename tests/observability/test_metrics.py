"""Tests for the metrics module."""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter

from signal_client.observability.metrics import (
    API_CLIENT_PERFORMANCE,
    CIRCUIT_BREAKER_STATE,
    COMMAND_LATENCY,
    COMMANDS_PROCESSED,
    DLQ_BACKLOG,
    DLQ_EVENTS,
    ERRORS_OCCURRED,
    MESSAGE_QUEUE_DEPTH,
    MESSAGE_QUEUE_LATENCY,
    MESSAGES_PROCESSED,
    RATE_LIMITER_WAIT,
    SHARD_QUEUE_DEPTH,
    WEBSOCKET_CONNECTION_STATE,
    WEBSOCKET_EVENTS,
    render_metrics,
)


def test_render_metrics_supports_custom_registry():
    """Test that render_metrics supports custom Prometheus registries."""
    registry = CollectorRegistry()
    counter = Counter("custom_counter", "help", registry=registry)  # type: ignore[name-defined]
    counter.inc()

    output = render_metrics(registry)
    assert "custom_counter" in output.decode("utf-8")


def test_render_metrics_uses_default_registry():
    """Test that render_metrics uses the default Prometheus registry."""
    MESSAGES_PROCESSED.inc()
    ERRORS_OCCURRED.inc()
    with API_CLIENT_PERFORMANCE.time():
        pass

    output = render_metrics()
    text = output.decode("utf-8")
    assert "messages_processed_total" in text
    assert "errors_occurred_total" in text


def test_new_metrics_can_be_recorded():
    """Test that new metrics can be recorded."""
    MESSAGE_QUEUE_DEPTH.set(5)
    MESSAGE_QUEUE_LATENCY.observe(0.05)
    DLQ_BACKLOG.labels(queue="signal_client_dlq").set(2)
    DLQ_EVENTS.labels(queue="signal_client_dlq", event="enqueued").inc()
    RATE_LIMITER_WAIT.observe(0.01)
    CIRCUIT_BREAKER_STATE.labels(endpoint="/messages", state="closed").set(1)
    WEBSOCKET_EVENTS.labels(event="connected").inc()
    WEBSOCKET_CONNECTION_STATE.set(1)
    COMMANDS_PROCESSED.labels(command="demo", status="success").inc()
    COMMAND_LATENCY.labels(command="demo", status="success").observe(0.01)
    SHARD_QUEUE_DEPTH.labels(shard="0").set(3)

    output = render_metrics()
    text = output.decode("utf-8")
    assert "message_queue_depth" in text
    assert "message_queue_latency_seconds_bucket" in text
    assert "dead_letter_queue_depth" in text
    assert "dlq_events_total" in text
    assert "rate_limiter_wait_seconds_bucket" in text
    assert "circuit_breaker_state" in text
    assert "websocket_events_total" in text
    assert "websocket_connection_state" in text
    assert "command_calls_total" in text
    assert "command_latency_seconds_bucket" in text
    assert "message_shard_queue_depth" in text
