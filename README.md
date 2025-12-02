# Signal Client

[![CI](https://github.com/cornellsh/signal-client/actions/workflows/ci.yml/badge.svg)](https://github.com/cornellsh/signal-client/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/signal_client.svg)](https://github.com/cornellsh/signal_client/blob/main/LICENSE)

Async Python framework for building Signal bots. The core loop consumes websocket messages, enqueues them with backpressure, fans out to workers, normalizes payloads, and dispatches command handlers that can call REST API clients or send replies via context helpers.

## Quickstart

```bash
poetry install --sync
export SIGNAL_PHONE_NUMBER=+1234567890
export SIGNAL_SERVICE_URL=https://signal.example.com
export SIGNAL_API_URL=https://signal.example.com
poetry run python -m signal_client.compatibility --strict  # optional guard
```

```python
from signal_client import SignalClient, command, Context

@command("!ping")
async def ping(ctx: Context) -> None:
    await ctx.reply({"message": "pong", "recipients": []})

bot = SignalClient()
bot.register(ping)
bot.run()
```

## Configuration

Settings are pydantic-based and loaded from env/.env, with aliases:

- `SIGNAL_PHONE_NUMBER` (required)
- `SIGNAL_SERVICE_URL` (required, ws/wss inferred)
- `SIGNAL_API_URL` (required, http/https)
- Storage: `STORAGE_TYPE` (`sqlite` default, `redis`), `SQLITE_DATABASE`, `REDIS_HOST`, `REDIS_PORT`
- Queue/backpressure: `QUEUE_SIZE` (default 1000), `QUEUE_PUT_TIMEOUT` (seconds), `QUEUE_DROP_OLDEST_ON_TIMEOUT` (default true)
- DLQ: `DLQ_NAME`, `DLQ_MAX_RETRIES`
- Circuit breaker, rate limiter, and API retry knobs are available under their respective prefixes.

## Backpressure and DLQ semantics

- Enqueue uses a timeout; on timeout the default behavior is lossy: drop the oldest message, then retry putting the new one. Set `queue_drop_oldest_on_timeout=False` to fail fast instead (dropped payloads go to DLQ if configured).
- DLQ entries now carry `retry_count` and an exponential backoff (`next_retry_at`). `replay()` only returns entries that are ready and under the max retry count.

## Command routing

- Command triggers are compiled into regexes sorted lexicographically, not by registration order. Prefer disjoint patterns or add explicit regex anchors to avoid surprises.

## Metrics

- Prometheus metrics are defined in `signal_client.metrics`. Expose them via the helper:

```python
from signal_client.metrics_server import start_metrics_server

start_metrics_server(port=9000, addr="0.0.0.0")
```

- This starts a lightweight HTTP endpoint at `/` that serves the Prometheus text format.

## Operations

- Local quality gate: `poetry run ruff check .`; `poetry run black --check src tests`; `poetry run mypy src`; `poetry run pytest-safe -n auto --cov=signal_client`.
- CI runs linting, formatting, mypy, security scans (`pip-audit`), unit/integration tests, API parity audits (`audit-api`), and `release-guard` on every push.
- `release-guard` blocks releases until compatibility notes/migrations are confirmed.
