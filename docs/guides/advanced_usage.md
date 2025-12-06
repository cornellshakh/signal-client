# Advanced Usage

Practical patterns for richer bots, middleware, and operations.

## Command handlers and routing
- Use `@command` to declare triggers. Strings are matched case-insensitively by default; pass `case_sensitive=True` or regex patterns for stricter routing.
- `whitelisted=["+15551234567"]` restricts who can run a command.
- Register commands on the client before calling `start()`:
```python
from signal_client import SignalClient, command

bot = SignalClient()

@command(r"^!echo\\s+(.+)$", case_sensitive=False)
async def echo(ctx):
    await ctx.reply_text(ctx.message.message or "")

bot.register(echo)
```

## Middleware
Wrap command execution with cross-cutting concerns such as logging, auth, or rate limiting:

```python
from collections.abc import Awaitable, Callable
from signal_client import Context, SignalClient

client = SignalClient()

async def log_middleware(ctx: Context, next_handler: Callable[[Context], Awaitable[None]]) -> None:
    print(f"handling {ctx.message.message!r} from {ctx.message.source}")
    await next_handler(ctx)
    print("done")

client.use(log_middleware)
```

Middleware are invoked in the order registered and wrap the underlying command handler.

## Context helpers
Every command receives a `Context` with typed helpers:
- Replies: `await ctx.reply_text("pong")`, `await ctx.send_markdown("*hi*")`, `await ctx.send_with_preview(url)`.
- Attachments: `async with ctx.download_attachments() as files:` yields temporary file paths for incoming attachments.
- Reactions and receipts: `await ctx.react("👍")`, `await ctx.send_receipt(ctx.message.timestamp)`.
- Typing indicators: `await ctx.show_typing()` / `await ctx.hide_typing()`.
- Distributed locks: `async with ctx.lock("resource-id"):` guards critical sections when `STORAGE_TYPE=redis` and locks are enabled.

## Concurrency and resiliency
- The worker pool fans out message handling; tune with `WORKER_POOL_SIZE`, `WORKER_SHARD_COUNT`, and `QUEUE_SIZE`.
- Enable persistence with `DURABLE_QUEUE_ENABLED=true` and either SQLite (`STORAGE_TYPE=sqlite`) or Redis (`STORAGE_TYPE=redis`).
- A Dead Letter Queue backs off and retries failures (`DLQ_MAX_RETRIES`, `DLQ_NAME`).
- Rate limiter and circuit breaker settings are surfaced via configuration (`RATE_LIMIT`, `CIRCUIT_BREAKER_*`).

## Health and metrics
- Start a basic health server to expose `/live`, `/ready`, and `/dlq`:
  ```python
  from signal_client.observability.health_server import start_health_server

  app = client.app  # after initialization
  await app.initialize()
  await start_health_server(app, port=8082)
  ```
- Export Prometheus metrics with `signal_client.observability.metrics_server.start_metrics_server(port=8000)`.

---

## 5. Request and Response Transformation

Beyond simple headers, you might need to fundamentally alter the JSON payload of requests or responses. This is particularly useful when integrating with APIs that have idiosyncratic data structures.

### Example: Transforming Outgoing Request Body

```python
import httpx
import json
from typing import Callable, Awaitable

async def transform_request_body(
    request: httpx.Request,
    call_next: Callable[[httpx.Request], Awaitable[httpx.Response]],
) -> httpx.Response:
    if request.method == "POST" and request.url.path == "/v1/messages":
        # Assume the API expects 'content' instead of 'message'
        original_json = json.loads(request.content)
        if "message" in original_json:
            original_json["content"] = original_json.pop("message")
            request.content = json.dumps(original_json).encode("utf-8")
            request.headers["Content-Length"] = str(len(request.content))
    response = await call_next(request)
    return response

# Use this with an event_hook for 'request'.
```

### Example: Transforming Incoming Response Body

```python
import httpx
import json
from typing import Callable, Awaitable

async def transform_response_body(
    response: httpx.Response,
    call_next: Callable[[httpx.Response], Awaitable[httpx.Response]],
) -> httpx.Response:
    if response.request.url.path == "/v1/users" and response.status_code == 200:
        # Assume the API returns 'user_data' but you want 'user'
        original_json = response.json()
        if "user_data" in original_json:
            original_json["user"] = original_json.pop("user_data")
            response._content = json.dumps(original_json).encode("utf-8")
            response.headers["Content-Length"] = str(len(response._content))
    return await call_next(response)

# Note: httpx's event_hooks for responses are processed after _raise_for_status,
# so direct modification of response._content is generally needed.
```

---

## 6. Advanced Asynchronous Patterns

Leverage Python's `asyncio` for concurrent operations when making multiple API calls.

```python
import asyncio
from signal_client.adapters.api.contacts_client import ContactsClient
from signal_client.adapters.api.messages_client import MessagesClient

async def fetch_contacts_and_send_messages(base_url: str, phone_number: str):
    contacts_client = ContactsClient(base_url=base_url)
    messages_client = MessagesClient(base_url=base_url)

    # Fetch contacts concurrently
    contacts_task = contacts_client.get_contacts(phone_number)
    messages_to_send = [
        {"recipient": "+1234567890", "message": "Hello!"},
        {"recipient": "+1987654321", "message": "How are you?"},
    ]
    send_message_tasks = [
        messages_client.send(msg) for msg in messages_to_send
    ]

    results = await asyncio.gather(contacts_task, *send_message_tasks)

    all_contacts = results[0]
    sent_messages_confirmations = results[1:]

    print("Contacts:", all_contacts)
    print("Sent Messages:", sent_messages_confirmations)

# To run:
# asyncio.run(fetch_contacts_and_send_messages("https://api.signal.com", "+11231231234"))
```

By mastering custom middleware and leveraging asynchronous programming, you can build highly robust, flexible, and performant applications with the Signal Client.
