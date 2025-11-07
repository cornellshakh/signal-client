# Observability

!!! info "Who should read this"
    Use this guide when you need to wire metrics, logs, or diagnostics into your deployment pipeline or dashboards.

Signal Client surfaces rich telemetry and diagnostics to keep production bots healthy.

## Prometheus Metrics

Metrics are registered in `signal_client.metrics` and share a single Prometheus registry.

| Metric | Type | Labels | Description |
| --- | --- | --- | --- |
| `MESSAGE_QUEUE_DEPTH` | Gauge | `queue` | Current queue size. |
| `MESSAGE_QUEUE_LATENCY` | Histogram | `worker` | Time between enqueue and dequeue. |
| `COMMAND_INVOCATIONS` | Counter | `command` | Successful command executions. |
| `DLQ_BACKLOG` | Gauge | `queue` | Pending DLQ messages. |
| `RATE_LIMITER_WAIT` | Histogram | `command` | Time spent waiting for rate limiter. |
| `CIRCUIT_BREAKER_STATE` | Gauge | `resource`, `state` | Current state per resource (`closed`, `open`, `half_open`). |

Export metrics using the standard Prometheus client:

```python
from prometheus_client import start_http_server

start_http_server(9102)
```

## Structured Logging

- Logging uses `structlog` with context variables.
- Each message binds `worker_id`, `command_name`, `queue_latency_seconds`, and `message_id`.
- Set `structured_logging=false` in settings to keep host logging untouched.

## Diagnostics

- `Settings.from_sources()` reports missing/invalid configuration with actionable errors.
- `compatibility.check_supported_versions()` throws on unsupported dependency versions; run it as part of CI to catch drifts early.
- `scripts/run_tests.py` forcibly terminates pytest to avoid hanging runner processes caused by background tasks.

## Instrumenting Custom Metrics

Access the shared registry through the container:

```python
registry = container.metrics_registry()
# Register additional collectors if necessary
```

Ensure custom metrics respect the namespace/prefix configured in settings to keep dashboards consistent.

## Alerting Suggestions

- Alert when `MESSAGE_QUEUE_DEPTH` stays above 80% capacity for more than a minute.
- Alert when `CIRCUIT_BREAKER_STATE{state="open"}` is non-zero for critical resources.
- Alert on elevated `MESSAGE_QUEUE_LATENCY` p95 or sustained growth in `DLQ_BACKLOG`.

For mitigation strategies, see the [Operations](./operations.md) runbooks.

---

**Next up:** Put these signals to work by following the [Operations](./operations.md) incident playbooks or explore the [API Reference](./api-reference.md) for customization hooks.
