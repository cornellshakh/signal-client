# Signal Client

[![CI](https://github.com/cornellsh/signal-client/actions/workflows/ci.yml/badge.svg)](https://github.com/cornellsh/signal-client/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/signal-client.svg)](https://pypi.org/project/signal-client/)
[![License](https://img.shields.io/pypi/l/signal_client.svg)](https://github.com/cornellsh/signal_client/blob/main/LICENSE)

**Signal Client is a Python runtime for building Signal bots.** It wraps [`signal-cli-rest-api`](https://github.com/bbernhard/signal-cli-rest-api) and gives you typed commands, background workers, retries, and observability in one package.

- `pip install signal-client`
- Documentation: https://cornellsh.github.io/signal-client/
- API Reference: https://cornellsh.github.io/signal-client/api-reference/

## What you get

- Register commands that react to messages in chats and groups.
- Send replies with attachments, mentions, and templated content.
- Run middleware before or after each command to check auth or feature flags.
- Schedule background jobs for reminders, clean-up tasks, or API polling.
- Keep bots healthy with worker pools, retries, and dead-letter queues.
- Export metrics and structured logs for dashboards and alerting.

## Get started in three steps

1. **Connect to `signal-cli-rest-api`.** Pair your bot account, enable JSON-RPC mode, and leave it running. The [Quickstart](https://cornellsh.github.io/signal-client/quickstart/) has copy-paste commands for Linux, macOS, and containers.
2. **Install and verify the runtime.**
   ```bash
   pip install signal-client
   python -m signal_client.compatibility --strict
   ```
3. **Register a simple command.**
   ```python
   import asyncio
   from signal_client.bot import SignalClient
   from signal_client.context import Context
   from signal_client.command import Command
   from signal_client.infrastructure.schemas.requests import SendMessageRequest

   async def main():
       # Initialize the Signal Client
       client = SignalClient()
       
       # Create a command that responds to "!ping"
       ping_command = Command(triggers=["!ping"])
       
       async def ping_handler(context: Context) -> None:
           """Reply with Pong."""
           response = SendMessageRequest(
               message="Pong! 🏓",
               recipients=[]  # Empty list replies to sender
           )
           await context.reply(response)
       
       # Register the command
       ping_command.with_handler(ping_handler)
       client.register(ping_command)
       
       # Start the bot
       await client.start()

   if __name__ == "__main__":
       asyncio.run(main())
   ```

Ready to keep going? Walk through the full setup in the [Quickstart guide](https://cornellsh.github.io/signal-client/quickstart/).

## Capabilities that matter day to day

- **Typed command context** keeps message bodies, attachments, sender info, and reply helpers in one object.
- **Worker pools, queues, and retries** prevent slow commands from stalling the rest of your bot.
- **Middleware hooks** add authentication, rate limits, keyword filters, or analytics without touching handlers.
- **Scheduled and background work** lets you poll APIs, post reminders, or clean up state on an interval.
- **Metrics and structured logs** give visibility into message throughput, failures, and retry loops.
- **Compatibility checks** block unsupported dependency versions before your bot boots.

Tour the runtime in the [Feature overview](https://cornellsh.github.io/signal-client/feature-tour/).

## Operations

- CI runs linting (`ruff`, `black`), type checks (`mypy`), security scans (`pip-audit`), tests, and MkDocs builds on every push.
- `release-guard` keeps publishing blocked until compatibility notes and migrations are confirmed.
- Observability guides explain dashboards, structured logs, and how to replay dead-letter queues after an outage.

### Releases

1. Update `pyproject.toml` and `docs/appendix/changelog.md` with the new version highlights.
2. Merge the change into `main`.
3. From GitHub → Actions → **Publish**, run the workflow on `main` (optionally paste release notes).

The workflow runs the full quality gate, publishes the build to PyPI via trusted publishing, and creates the Git tag/GitHub release (attaching the built distributions). Pushing a `v*.*.*` tag manually will trigger the same automation.

## Documentation & support

- Documentation hub: https://cornellsh.github.io/signal-client/
- Key guides: [Quickstart](https://cornellsh.github.io/signal-client/quickstart/) · [Configuration](https://cornellsh.github.io/signal-client/configuration/) · [Operations](https://cornellsh.github.io/signal-client/operations/)
- Ask questions or request features via [Discussions](https://github.com/cornellsh/signal-client/discussions) or [Issues](https://github.com/cornellsh/signal-client/issues)

## Supported versions

- **Python:** 3.9 – 3.13
- **Dependency Injector:** 4.41.x – 4.48.x
- **Structlog:** 24.1.x – 24.4.x
- **Pydantic:** 2.11.x – 2.12.x

The runtime refuses to start when versions fall outside these ranges so you catch drift early. Override only when you fully control deployment boundaries.

## Stay in touch

- Documentation hub: https://cornellsh.github.io/signal-client/
- Architecture notes: [Overview](https://cornellsh.github.io/signal-client/overview/) · [Architecture](https://cornellsh.github.io/signal-client/architecture/)
- Command patterns: [Writing Async Commands](https://cornellsh.github.io/signal-client/guides/writing-async-commands/)

Maintained by [@cornellsh](https://github.com/cornellsh). If Signal Client powers something helpful, open a discussion or drop an issue—I’d love to hear about it.
