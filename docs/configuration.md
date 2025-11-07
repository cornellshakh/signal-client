# Configuration

!!! info "Who should read this"
    Consult this reference when you are configuring Signal Client for staging/production, tuning runtime limits, or wiring external services.

Signal Client reads configuration through the Pydantic `Settings` model (`signal_client.config.Settings`). Values can come from `SignalClient(config=...)`, environment variables, or `.env` files.

## Core Connectivity

| Setting | Env Var | Description |
| --- | --- | --- |
| `signal_service` | `SIGNAL_SERVICE` | Base URL of `signal-cli-rest-api`. |
| `phone_number` | `SIGNAL_PHONE_NUMBER` | Bot phone number in E.164 format. |
| `trust_all_certificates` | `SIGNAL_TRUST_ALL_CERTS` | Skip TLS verification (local testing only). |

## Worker & Queue Controls

| Setting | Default | Notes |
| --- | --- | --- |
| `worker_pool_size` | `4` | Number of concurrent workers consuming the queue. |
| `message_queue_maxsize` | `200` | Upper bound before back-pressure engages. |
| `backpressure_strategy` | `"block"` | Options: `block`, `drop_oldest`, `reject`. |
| `queue_latency_alert_seconds` | `5.0` | Emit warning logs when exceeded. |

## Rate Limiter

```json
{
  "rate_limiter": {
    "rate_limit": 2,
    "period": 1.0
  }
}
```

- `rate_limit`: Maximum operations per `period` seconds.
- Metrics surface in `RATE_LIMITER_WAIT` histogram.

## Circuit Breaker

```json
{
  "circuit_breaker": {
    "failure_threshold": 5,
    "reset_timeout": 30.0,
    "rolling_window": 60.0
  }
}
```

- Each resource key (e.g., `messages`) has an independent breaker.
- States are exported via `CIRCUIT_BREAKER_STATE` gauge.

## Dead Letter Queue

```json
{
  "dead_letter_queue": {
    "max_retries": 5,
    "initial_backoff": 5.0,
    "backoff_multiplier": 2.0,
    "maximum_backoff": 300.0,
    "jitter": 0.1
  }
}
```

- Controls DLQ retry cadence and backlog reporting.
- Combine with storage providers to persist beyond memory.

## Storage Providers

```json
{
  "storage": {
    "provider": "redis",
    "redis": {"url": "redis://localhost:6379/0"},
    "sqlite": {"path": "queue.db"}
  }
}
```

- Providers: `memory`, `redis`, `sqlite`.
- Redis uses URLs; SQLite stores on disk.

## Observability Toggles

| Setting | Default | Description |
| --- | --- | --- |
| `metrics_enabled` | `true` | Disable to skip Prometheus registration. |
| `metrics_namespace` | `"signal_client"` | Prefix for metric names. |
| `log_level` | `"INFO"` | Default structlog level. |
| `structured_logging` | `true` | Skip internal `structlog.configure()` if host app manages logging. |

## Release Guardrails

| Setting | Default | Description |
| --- | --- | --- |
| `enforce_compatibility` | `true` | When false, skip `check_supported_versions()` (not recommended). |
| `release_guard_keywords` | `"BREAKING CHANGE"` | Additional phrases that trigger release guard failure. |

## Example Configuration

```python
from signal_client import SignalClient

client = SignalClient(
    {
        "signal_service": "https://signal-gateway.internal",
        "phone_number": "+15558675309",
        "worker_pool_size": 8,
        "message_queue_maxsize": 500,
        "backpressure_strategy": "drop_oldest",
        "rate_limiter": {"rate_limit": 10, "period": 60.0},
        "circuit_breaker": {"failure_threshold": 8, "reset_timeout": 45.0},
        "dead_letter_queue": {
            "max_retries": 6,
            "initial_backoff": 10.0,
            "backoff_multiplier": 1.5,
            "maximum_backoff": 600.0,
        },
        "storage": {
            "provider": "redis",
            "redis": {"url": "redis://redis:6379/0"},
        },
    }
)
```

Missing required values raise detailed `ValidationError`s listing absent environment variables and expected types. See [Observability](./observability.md) for metrics details and [Operations](./operations.md) for scaling guidance.

---

**Next up:** Wire metrics and structured logs via [Observability](./observability.md) or plan your rollout with [Operations](./operations.md).
