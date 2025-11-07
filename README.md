# Signal Client

[![CI](https://github.com/cornellsh/signal-client/actions/workflows/ci.yml/badge.svg)](https://github.com/cornellsh/signal-client/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/signal-client.svg)](https://pypi.org/project/signal-client/)
[![License](https://img.shields.io/pypi/l/signal_client.svg)](https://github.com/cornellsh/signal_client/blob/main/LICENSE)

**Build Signal automations that feel bespoke without rebuilding production plumbing.** Signal Client wraps [`signal-cli-rest-api`](https://github.com/bbernhard/signal-cli-rest-api) with a resilient async runtime, typed command surface, and observability that scales from hobby bots to high-volume workflows.

- `pip install signal-client`
- Documentation: https://cornellsh.github.io/signal-client/
- API Reference: https://cornellsh.github.io/signal-client/api-reference/

## What you can build

| Scenario | Outcome |
| --- | --- |
| Customer ops automations | Route incoming messages to the right teammate with alerts, audit logs, and retries baked in. |
| Notification pipelines | Fan out incident or release notifications with guardrails that pause noisy queues and surface metrics immediately. |
| Workflow assistants | Prototype assistants that enrich or respond to chats using middleware and typed contexts without blocking the event loop. |

## Getting started in 3 steps

1. **Launch `signal-cli-rest-api`** (link, pair, restart in JSON-RPC) — see the [Quickstart](./docs/quickstart.md) for copy-paste commands.
2. **Install and verify**:
   ```bash
   pip install signal-client
   python -m signal_client.compatibility
   ```
3. **Register a command**:
   ```python
   from signal_client import SignalClient, Context

   class PingCommand:
       triggers = ["!ping"]

       async def handle(self, context: Context) -> None:
           await context.reply("Pong!")

   client = SignalClient({
       "signal_service": "http://localhost:8080",
       "phone_number": "+1234567890",
       "worker_pool_size": 4,
   })
   client.register(PingCommand())
   ```

Ready for the full walkthrough? Head to the [Quickstart guide](https://cornellsh.github.io/signal-client/quickstart/).

## Feature highlights

- **Command-first developer experience:** Regex and string triggers, typed `Context` objects, and before/after middleware layers.
- **Production resilience built-in:** Back-pressure controls, bounded worker pools, DLQ replay helpers, rate limiting, and circuit breakers.
- **Observability that speaks SRE:** Prometheus metrics, structured logging with worker metadata, and compatibility guards that fail fast.
- **Release guardrails:** Semantic version and dependency matrix enforcement keep breaking changes out of production by default.

Explore the [Feature Tour](https://cornellsh.github.io/signal-client/feature-tour/) for a visual walkthrough of the runtime layers.

## Production proof points

- CI runs linting (`ruff`, `black`), static typing (`mypy`), security scans (`pip-audit`), tests, and MkDocs builds on every push.
- `release-guard` blocks publishing if compatibility promises or migrations aren’t acknowledged.
- Observability guide covers metrics dashboards, log enrichment, and live debugging recipes.

Dig deeper via the [Operations runbook](https://cornellsh.github.io/signal-client/operations/) and [Observability guide](https://cornellsh.github.io/signal-client/observability/).

## Compatibility matrix

- **Python:** 3.9 – 3.13
- **Dependency Injector:** 4.41.x – 4.48.x
- **Structlog:** 24.1.x – 24.4.x
- **Pydantic:** 2.11.x – 2.12.x

The runtime refuses to start when these versions drift. Override checks only if you fully control deployment boundaries.

## Learn more

- Documentation hub: https://cornellsh.github.io/signal-client/
- Use cases & architecture: [Overview](https://cornellsh.github.io/signal-client/overview/) · [Architecture](https://cornellsh.github.io/signal-client/architecture/)
- Command patterns: [Writing Async Commands](https://cornellsh.github.io/signal-client/guides/writing-async-commands/)

Maintained by [@cornellsh](https://github.com/cornellsh). If Signal Client powers something cool, open a discussion or drop a note in the issue tracker—I’d love to feature it.
