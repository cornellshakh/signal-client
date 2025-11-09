---
title: Writing Async Commands
summary: Register, test, and deploy custom Signal Client commands.
order: 200
---

## Create a command

Commands in Signal Client are created using the `Command` class and registered with the `SignalClient`:

/// tab | Python

    :::python
    from signal_client.bot import SignalClient
    from signal_client.context import Context
    from signal_client.command import Command

    # Create a command that responds to "greet" or "hello"
    greet_command = Command(triggers=["greet", "hello"])

    async def greet_handler(context: Context) -> None:
        """Greet the user."""
        from signal_client.infrastructure.schemas.requests import SendMessageRequest
        
        response = SendMessageRequest(
            message="Hey there! 👋",
            recipients=[]  # Empty list replies to sender
        )
        await context.reply(response)

    # Attach the handler to the command
    greet_command.with_handler(greet_handler)
///

/// tab | TypeScript (REST caller)

    :::typescript
    import fetch from "node-fetch";

    await fetch("http://localhost:8080/v2/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: "Hey there! 👋",
        recipients: ["+19998887777"],
        number: process.env.SIGNAL_NUMBER,
      }),
    });
///

## Register with the client

```python
from signal_client.bot import SignalClient
from signal_client.context import Context
from signal_client.command import Command

# Initialize the client
client = SignalClient()

# Create and register the command
greet_command = Command(triggers=["greet", "hello"])

async def greet_handler(context: Context) -> None:
    """Greet the user."""
    from signal_client.infrastructure.schemas.requests import SendMessageRequest
    
    response = SendMessageRequest(
        message="Hey there! 👋",
        recipients=[]  # Empty list replies to sender
    )
    await context.reply(response)

greet_command.with_handler(greet_handler)
client.register(greet_command)

if __name__ == "__main__":
    import asyncio
    asyncio.run(client.start())
```

!!! tip "Use dependency injection"

## Core workflows

### Messaging

1. Inspect `context.message` to understand sender, group, and attachments.
2. Compose a reply with `context.reply`, `context.send_attachment`, or `context.reaction`.
3. Record success metrics and exit early on duplicate message IDs.

/// tab | Python

    :::python
    async def ticket_ack(context: Context) -> None:
        # Access message data through context.message
        sender = context.message.source
        
        from signal_client.infrastructure.schemas.requests import SendMessageRequest
        response = SendMessageRequest(
            message=f"Ticket acknowledged from {sender} ✅",
            recipients=[]  # Reply to sender
        )
        await context.reply(response)
        # Metrics and logging can be added through dependency injection
///

/// tab | TypeScript (REST caller)

    :::typescript
    await fetch("http://localhost:8080/v2/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: `Ticket ${payload.ticketId} acknowledged ✅`,
        recipients: [payload.sender],
        number: process.env.SIGNAL_NUMBER,
      }),
    });
///

/// codexec

    :::python
    print("Sample Signal Client command registered")
///

### Group management

- +heroicons:user-group+ Create or update groups through the REST bridge (`/v1/groups`) before inviting the runtime bot.
- Maintain a registry of group IDs in SQLite or Redis for quick lookups.
- Use commands to add or remove members by emitting REST calls via an injected service.

```python
await context.groups.add_member(group_id="support-escalation", number="+44123456789")
```

### Media and attachments

1. Upload large files through the REST bridge and capture the returned attachment handle.
2. Reference the handle when sending via `context.send_attachment`.
3. Store handles in persistent storage if you need to reuse them later.

```python
handle = await context.attachments.upload(path="reports/outage.pdf")
await context.send_attachment(handle=handle, caption="Outage summary")
```

### Webhooks and external triggers

- Expose a FastAPI or Flask endpoint that integrates with your Signal Client.
- Validate signatures and rate limit external callers to protect worker capacity.
- Use the Signal Client's messaging capabilities to forward notifications.

```python
from fastapi import FastAPI
from signal_client.bot import SignalClient

app = FastAPI()
client = SignalClient()

@app.post("/hooks/status")
async def status_hook(payload: dict) -> None:
    # Process webhook and send Signal message
    # Implementation depends on your specific use case
    pass
```

!!! tip "Dependency injection"
    Commands accept a `Context` argument which provides access to all Signal Client services and the current message context.

## Test locally

1. Start the REST bridge (see [Quickstart](../quickstart.md)).
2. Run your Signal Client application with your registered commands.
3. Send yourself a test message matching your command triggers and confirm the command replies as expected.

```python
# Example: test_bot.py
import asyncio
from signal_client.bot import SignalClient
from signal_client.context import Context
from signal_client.command import Command

async def main():
    client = SignalClient()
    
    # Register your test command
    test_command = Command(triggers=["test"])
    
    async def test_handler(context: Context) -> None:
        await context.reply("Test command working! ✅")
    
    test_command.with_handler(test_handler)
    client.register(test_command)
    
    # Start the client
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())
```

[=50% "Command verified"]{: .warning}

## Harden before production

- Add idempotency by checking `context.message.timestamp` or message content against your data store.
- Implement proper error handling and logging for production reliability.
- Guard against abuse: validate message length and rate limit per sender.
- Use middleware for cross-cutting concerns like authentication and rate limiting.

!!! warning "Watch your exception handlers"
    Swallowing exceptions hides DLQ-worthy issues. Allow them to propagate so the runtime retries or escalates appropriately.

[=100% "Production ready"]{: .success}

> **Next step** · Document and export your command interface in [API Reference](../api-reference.md).
