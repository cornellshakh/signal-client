# signal-client — Async Signal bot framework

[![PyPI version](https://img.shields.io/pypi/v/signal-client)](https://pypi.org/project/signal-client/)
[![Python versions](https://img.shields.io/pypi/pyversions/signal-client)](https://pypi.org/project/signal-client/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-latest-blue)](https://cornellsh.github.io/signal-client/)

Async framework for Signal bots on top of `signal-cli-rest-api`. Provides websocket ingestion with backpressure, typed helpers for replies/attachments/reactions, and resilience primitives (durable queues, rate limiting, circuit breakers) so bots stay healthy. Defaults favor safety and PII redaction; contributors are welcome via issues and PRs.

## Prerequisites

- A Signal phone number registered with `signal-cli`.
- A running [`bbernhard/signal-cli-rest-api`](https://github.com/bbernhard/signal-cli-rest-api) instance (websocket + REST).
- Environment variables:
  - `SIGNAL_PHONE_NUMBER` — the Signal number for your bot.
  - `SIGNAL_SERVICE_URL` — websocket host for receive (e.g., `http://localhost:8080`).
  - `SIGNAL_API_URL` — REST host for send (e.g., `http://localhost:8080`).
  - Optional: `STORAGE_TYPE` (`memory`|`sqlite`|`redis`), `REDIS_HOST`, `REDIS_PORT`, `DURABLE_QUEUE_ENABLED=true`.

## Installation

- PyPI: `pip install signal-client`
- Poetry: `poetry add signal_client`
- From source: `poetry install`

## Quickstart

1. Export configuration (or add to a `.env`):
   ```bash
   export SIGNAL_PHONE_NUMBER=+15551234567
   export SIGNAL_SERVICE_URL=http://localhost:8080
   export SIGNAL_API_URL=http://localhost:8080
   ```
2. Create a bot:

   ```python
   import asyncio
   from signal_client import SignalClient, command

   @command("!ping")
   async def ping(ctx):
       await ctx.reply_text("pong")

   async def main():
       bot = SignalClient()
       bot.register(ping)
       await bot.start()

   if __name__ == "__main__":
       asyncio.run(main())
   ```

3. Run it (or use `examples/ping_bot.py`): `poetry run python examples/ping_bot.py`

## Configuration highlights

- Queues: `QUEUE_SIZE`, `DURABLE_QUEUE_ENABLED`, `DURABLE_QUEUE_MAX_LENGTH`, `INGEST_PAUSE_SECONDS`.
- Resiliency: `RATE_LIMIT`, `RATE_LIMIT_PERIOD`, circuit breaker knobs (`CIRCUIT_BREAKER_*`).
- Storage: `STORAGE_TYPE` (`memory` default, `sqlite`, `redis`), `SQLITE_DATABASE`, `REDIS_HOST`, `REDIS_PORT`.
- Logging and redaction: `LOG_REDACTION_ENABLED` (defaults to true).

## Documentation

- Public site: https://cornellsh.github.io/signal-client/
- Local preview: `poetry run mkdocs serve`

## Development

- Install: `poetry install`
- Lint/format: `poetry run ruff check .`
- Types: `poetry run mypy src`
- Tests: `poetry run pytest`
- Docs: `poetry run mkdocs build`
- Pre-commit: set the hook once with either:
  - `git config core.hooksPath .githooks` (uses the bundled hook that shells into `poetry run pre-commit`)
  - or unset hooksPath and run `poetry run pre-commit install --install-hooks`

## Releasing

- Validate before cutting a release: `poetry check`, `poetry run ruff check .`, `poetry run mypy src`, `poetry run pytest`, `poetry run mkdocs build`
- Build artifacts: `poetry build`
- Semantic release automation is configured in `pyproject.toml` (`python-semantic-release`),
