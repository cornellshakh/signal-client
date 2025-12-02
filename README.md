# Signal Client

[![CI](https://github.com/cornellsh/signal-client/actions/workflows/ci.yml/badge.svg)](https://github.com/cornellsh/signal-client/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/signal_client.svg)](https://github.com/cornellsh/signal_client/blob/main/LICENSE)

Async Python framework for building Signal bots. The core loop consumes websocket messages, enqueues them with explicit backpressure, fans out to workers, normalizes payloads, and dispatches command handlers that can call REST API clients or send replies via context helpers.

## Quickstart

### Run the Signal backend (signal-cli-rest-api)

This library expects a running [bbernhard/signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) instance for both the websocket stream and REST endpoints.

1) Create a persistent config directory so re-creating the container does not lose your registration:

```bash
mkdir -p $HOME/.local/share/signal-api
```

2) Start the REST API (native mode is fast on most platforms):

```bash
docker run -d --name signal-api --restart=always -p 8080:8080 \
  -v $HOME/.local/share/signal-api:/home/.local/share/signal-cli \
  -e 'MODE=native' bbernhard/signal-cli-rest-api:latest
```

3) Link or register your Signal number:
- Easiest: open `http://localhost:8080/v1/qrcodelink?device_name=signal-api` and pair this container as a linked device in the Signal mobile app (Settings → Linked Devices → +).
- Alternatively: use `/v1/register/<number>` + `/v1/verify/<number>` if registering this container as primary (see upstream README for details).

4) Smoke test the REST API:

```bash
curl -X POST -H "Content-Type: application/json" 'http://localhost:8080/v2/send' \
  -d '{"message": "hello from signal-cli-rest-api", "number": "+15551234567", "recipients": ["+15557654321"]}'
```

5) Configure `signal-client` to point at the REST API (HTTP will be converted to ws/wss for the websocket stream):

```bash
poetry install --sync
export SIGNAL_PHONE_NUMBER=+1234567890
export SIGNAL_SERVICE_URL=http://localhost:8080
export SIGNAL_API_URL=http://localhost:8080
```

```python
import asyncio

from signal_client import Context, SignalClient, command
from signal_client.infrastructure.schemas.requests import SendMessageRequest


@command("!ping")
async def ping(ctx: Context) -> None:
    await ctx.reply(SendMessageRequest(message="pong", recipients=[]))


async def main() -> None:
    async with SignalClient() as bot:
        bot.register(ping)
        await bot.start()


asyncio.run(main())
```

## Architecture at a glance
- `signal_client/config.py`: single pydantic `Settings` mapping required env vars and runtime knobs.
- `signal_client/app.py`: explicit builder wiring settings → websocket listener → queue/backpressure → worker pool/router → API clients/storage.
- `signal_client/runtime/`: listener, backpressure policy, worker pool, command router, middleware hooks, queue models.
- `signal_client/api/` + `signal_client/infrastructure/api_clients/`: REST clients; shared `ClientConfig`.
- `signal_client/storage/`: sqlite/redis backends and DLQ helpers.
- `signal_client/observability/`: metrics (Prometheus) and structlog bootstrap.

## Configuration

Settings are pydantic-based and loaded from env/.env via `Settings.from_sources(config=overrides)`.

- Required: `SIGNAL_PHONE_NUMBER`, `SIGNAL_SERVICE_URL` (ws/wss inferred), `SIGNAL_API_URL` (http/https)
- Storage: `STORAGE_TYPE` (`sqlite` default, or `redis`), `SQLITE_DATABASE`, `REDIS_HOST`, `REDIS_PORT`
- Queue/backpressure: `QUEUE_SIZE` (default 1000), `QUEUE_PUT_TIMEOUT` seconds, `QUEUE_DROP_OLDEST_ON_TIMEOUT` (default true), `WORKER_POOL_SIZE`
- DLQ: `DLQ_NAME`, `DLQ_MAX_RETRIES`
- API resiliency: `API_RETRIES`, `API_BACKOFF_FACTOR`, `API_TIMEOUT`, rate limiter and circuit breaker knobs (`RATE_LIMIT`, `RATE_LIMIT_PERIOD`, `CIRCUIT_BREAKER_*`)

## Backpressure and DLQ semantics

- Backpressure is explicit: enqueue waits up to `queue_put_timeout` and then either fails fast or drops the oldest item depending on `queue_drop_oldest_on_timeout` (maps to `BackpressurePolicy.FAIL_FAST` vs `DROP_OLDEST`). Dropped payloads are routed to the DLQ when configured.
- DLQ entries carry `retry_count` and `next_retry_at` with exponential backoff; `replay()` only returns entries ready for processing and below `dlq_max_retries`.

## Command routing

- Command triggers preserve registration order. Regex triggers are evaluated after literal triggers in the order they were registered.

## Metrics

- Prometheus metrics live in `signal_client.observability.metrics`. Expose them via:

```python
from signal_client.observability.metrics import start_metrics_server

start_metrics_server(port=9000, addr="0.0.0.0")
```

- Defaults to `addr="127.0.0.1"` and `port=8000`; pass a registry to expose custom metrics.
- This starts a lightweight HTTP endpoint at `/` that serves the Prometheus text format.

## CLI

- Minimal DLQ tooling is available via `python -m signal_client.cli dlq inspect` (or `poetry run inspect-dlq`).

## Operations

- Local quality gate: `poetry run ruff check .`; `poetry run black --check src tests`; `poetry run mypy src`; `poetry run pytest-safe -n auto --cov=signal_client`.
- CI runs linting, formatting, mypy, security scans (`pip-audit`), unit/integration tests, API parity audits (`audit-api`), and `release-guard` on every push.
- `release-guard` blocks releases until compatibility notes/migrations are confirmed.
