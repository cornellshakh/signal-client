# Operations & Deployment

How to run `signal-client` in production alongside `signal-cli-rest-api`.

## Runtime shape
- Websocket listener pulls messages from `signal-cli-rest-api` at `SIGNAL_SERVICE_URL`.
- Messages enter a backpressured queue and are processed by a worker pool.
- Failures backoff into a Dead Letter Queue (DLQ) with retries.
- API calls go through a rate limiter and circuit breaker.

## Environment
Use environment variables (or a `.env`) to configure the runtime:

```bash
SIGNAL_PHONE_NUMBER=+15551234567
SIGNAL_SERVICE_URL=http://localhost:8080   # websocket host
SIGNAL_API_URL=http://localhost:8080       # REST host
STORAGE_TYPE=sqlite                        # memory | sqlite | redis
DURABLE_QUEUE_ENABLED=true                 # persist ingest queue
DLQ_MAX_RETRIES=5
RATE_LIMIT=50
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
LOG_REDACTION_ENABLED=true
```

## Storage and backpressure
- **Memory (default):** best for local development; no durability.
- **SQLite:** `STORAGE_TYPE=sqlite` and optional `SQLITE_DATABASE=signal_client.db` for single-node durability.
- **Redis:** `STORAGE_TYPE=redis` plus `REDIS_HOST`/`REDIS_PORT` to unlock distributed locks and shared queues.
- Enable ingestion persistence with `DURABLE_QUEUE_ENABLED=true`; tune `QUEUE_SIZE` and `DURABLE_QUEUE_MAX_LENGTH` for your workload.

## Health and metrics
- Health endpoints: `HealthServer` exposes `/live`, `/ready`, and `/dlq` (choose a port like `8082`).
- Metrics: `signal_client.observability.metrics_server.start_metrics_server(port=8000)` publishes Prometheus metrics for websocket connectivity, queue depth, DLQ, and command latency.

## Running the process
- Package or install the project (`pip install signal-client` or `poetry install`) and run your bot entrypoint with a process manager (systemd, supervisord, Docker).
- Example service command: `poetry run python examples/ping_bot.py`
- Graceful shutdown: send SIGTERM/SIGINT; the client drains the queue, stops workers, and closes the websocket and HTTP session.

## Security and hardening
- Do not expose `signal-cli-rest-api` publicly; place it behind a firewall or private network.
- Keep secrets (auth tokens, phone numbers) in environment or a secrets manager.
- Enable log redaction in production (`LOG_REDACTION_ENABLED=true`) to avoid leaking PII.
