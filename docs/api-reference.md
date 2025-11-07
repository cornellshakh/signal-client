# API Reference

!!! info "Who should read this"
    Consult this catalog when you’re wiring Signal Client into an existing codebase, integrating with other services, or exploring the CLI utilities.

This reference highlights the primary classes, helpers, and CLI tooling exposed by Signal Client.

## SignalClient (`signal_client.bot.SignalClient`)

| Method | Description |
| --- | --- |
| `__init__(config: dict | None = None, container: Container | None = None)` | Bootstraps container, enforces compatibility, loads settings. |
| `register(command: Command)` | Adds a command instance by identity. |
| `use(middleware)` | Registers middleware with signature `async def middleware(context, call_next)`. |
| `start()` | Starts message service and worker pool; returns when shutting down. |
| `shutdown()` | Closes websocket, drains queue, stops workers, and closes aiohttp session. |
| `__aenter__`/`__aexit__` | Async context manager for scoped execution. |

## Command Protocol (`signal_client.command.Command`)

```python
class Command(Protocol):
    triggers: list[str | re.Pattern]
    whitelisted: list[str] | None
    case_sensitive: bool

    async def handle(self, context: Context) -> None: ...
    async def before_handle(self, context: Context) -> None: ...
    async def after_handle(self, context: Context) -> None: ...
```

- `triggers` may be strings or compiled regex patterns.
- Optional pre/post hooks integrate with middleware when defined.

## Context (`signal_client.context.Context`)

Attributes:

- `raw: QueuedMessage`
- `message: Message`
- `logger: structlog.BoundLogger`
- `clients`: namespace for REST clients (`messages`, `groups`, etc.)
- `locks`: access to shared locks via `LockManager`

Helpers:

- `reply(text, **kwargs)` / `send(text, recipients=None, **kwargs)`
- `react(emoji)` / `remove_reaction()`
- `start_typing()` / `stop_typing()`
- `rate_limit()` async context manager
- `circuit_breaker(resource)` async context manager
- `defer(callable, *args, **kwargs)` for post-command callbacks

## Compatibility Guard (`signal_client.compatibility`)

- `check_supported_versions()` — Throws if dependency-injector, structlog, or pydantic fall outside the approved ranges.
- CLI usage: `python -m signal_client.compatibility`.

## Release Guard (`signal_client.release_guard`)

- `enforce_pre_release_policy(commits)` — Blocks pre-1.0 releases that include breaking changes without appropriate markers.
- CLI: `poetry run release-guard --since <tag>`.

---

**Next up:** Return to the [Operations](./operations.md) runbooks for deployment practices or explore [Use Cases](./use-cases.md) to see these APIs in action.

## Metrics (`signal_client.metrics`)

Exports Prometheus collectors described in [Observability](./observability.md). Use `generate_latest()` or expose via HTTP server.

## Services

- `signal_client.services.message_service.MessageService` — websocket ingestion.
- `signal_client.services.worker_pool_manager.WorkerPoolManager` — bounded concurrency orchestrator.
- `signal_client.services.dead_letter_queue.DeadLetterQueue` — failure persistence and replay.
- `signal_client.services.rate_limiter.RateLimiter` — async token bucket.
- `signal_client.services.circuit_breaker.CircuitBreaker` — resilient HTTP execution.

## REST API Clients

Located under `signal_client.infrastructure.api_clients.*`; each maps 1:1 to `signal-cli-rest-api` resources (accounts, messages, groups, profiles, etc.). Methods return JSON or schema instances and raise domain-specific exceptions defined in `signal_client.exceptions`.

## CLI Entrypoints (`pyproject.toml` scripts)

| Command | Description |
| --- | --- |
| `poetry run inspect-dlq` | Inspect, replay, or export DLQ payloads. |
| `poetry run pytest-safe` | Run the test suite with safe teardown. |
| `poetry run release-guard` | Enforce pre-release policy before semantic-release. |
| `poetry run audit-api` | Ping REST endpoints for coverage verification. |

For implementation details, inspect the corresponding modules or the integration tests under `tests/`.
