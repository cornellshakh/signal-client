# Operations

!!! info "Who should read this"
    Reference these runbooks when you are operating Signal Client in staging/production or preparing for incident response.

Runbooks and procedures for keeping Signal Client deployments healthy.

## Monitor Queue Pressure

1. Watch `MESSAGE_QUEUE_DEPTH` and `MESSAGE_QUEUE_LATENCY` for rising trends.
2. Review logs for warnings tagged with `queue_latency_seconds`.
3. Mitigation options:
   - Increase `worker_pool_size` cautiously (see below).
   - Switch `backpressure_strategy` to `drop_oldest` during bursts.
   - Replay DLQ after dependencies stabilise.

## Scale Worker Pool

1. Evaluate current load and rate-limiter wait times.
2. Bump `worker_pool_size` in small increments and redeploy.
3. Validate that `RATE_LIMITER_WAIT` stays acceptable; adjust rate limiter thresholds if necessary.
4. Confirm host resource limits (FDs, CPU) are sufficient.

## Rotate Credentials

1. Pause ingestion (`SignalClient.shutdown()` or drain queue).
2. Export/inspect DLQ to ensure critical messages are handled.
3. Rotate secrets via your provider (Vault, AWS Secrets Manager, etc.).
4. Restart process; compatibility guard runs automatically at boot.
5. Monitor logs for authentication errors post-rotation.

## Replay the Dead Letter Queue

1. Check `DLQ_BACKLOG` gauge and logs for `dlq.retry_due_at` entries.
2. Validate upstream availability.
3. Trigger replay:
   ```bash
   poetry run inspect-dlq replay --max 50
   ```
4. Monitor queue depth/latency; repeat until backlog is cleared.

## Release Checklist

1. CI must pass lint (`ruff`), format (`black`), type-check (`mypy`), tests (`pytest-safe`), security audit (`pip-audit`), docs build (MkDocs), and `release-guard`.
2. For pre-1.0 versions, inspect commits for `!` or `BREAKING CHANGE` markers before publishing.
3. Build artifacts via `poetry build`; verify contents if distributing privately.
4. Rollbacks: revert the commit, rerun CI, and publish a corrective release.

## Incident Response Quick Links

- **Compatibility guard failure:** `python -m signal_client.compatibility --json`
- **Circuit breaker stuck open:** inspect `CIRCUIT_BREAKER_STATE` and logs for failing resource keys.
- **High rate limiter wait:** adjust quotas or rate limiter thresholds.
- **Metrics offline:** ensure Prometheus exporter is running and `metrics_enabled=true`.

For additional context on telemetry, see [Observability](./observability.md). Configuration details live in [Configuration](./configuration.md).

---

**Next up:** Explore the [API Reference](./api-reference.md) for tooling that supports these runbooks, or return to the [Use Cases](./use-cases.md) page to see how teams combine these practices.
