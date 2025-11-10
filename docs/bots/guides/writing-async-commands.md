# Writing Async Commands

## Guidelines

1. Always declare handlers with `async def` and use await for IO.
2. Accept a `context` parameter to access DI-provided collaborators.
3. Return structured responses (text, attachments, metadata) via helpers.

## Template

```python
from signal_client.command import CommandContext

@bot.command("status")
async def status(context: CommandContext, payload):
    service = await context.services.lookup(payload.service_id)
    await context.reply(f"{service.name} is healthy")
```

## Error handling

Use structured logging and raise domain-specific exceptions to trigger retries.

```python
import structlog
logger = structlog.get_logger(__name__)

@bot.command("sync")
async def sync(context, payload):
    try:
        await context.sync(payload.resource)
    except context.SyncError as exc:
        logger.warning("sync.failed", resource=payload.resource, error=str(exc))
        raise
```

Document preconditions and fallback paths in the command docstrings so mkdocstrings surfaces them.
