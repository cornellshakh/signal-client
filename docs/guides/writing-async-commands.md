# Writing Async Commands

!!! info "Who should read this"
    Use this guide when crafting new commands or refactoring existing ones to ensure they remain asynchronous and production-safe.

Signal Client runs entirely on `asyncio`; commands must never block the event loop. Follow these practices to keep workers responsive.

## Golden Rule

- **Do not block the event loop.** Avoid synchronous HTTP calls, file I/O, long-running CPU work, or `time.sleep()`.
- Prefer async equivalents (`aiohttp`, `aiofiles`, `asyncio.sleep()`).

## Helpers from Context

- `await context.rate_limit()` — honours shared rate limiter.
- `async with context.circuit_breaker("messages"):` — wraps outbound calls with failure tracking.
- `await context.defer(callback, *args)` — schedule side effects after command execution.

## Example: Fetching Data

```python
import asyncio
from signal_client import Command, Context

class WeatherCommand:
    triggers = ["!weather (?P<city>.*)"]

    async def handle(self, context: Context) -> None:
        city = context.message.data.match.group("city")
        async with context.circuit_breaker("weather_api"):
            await context.rate_limit()
            async with context.clients.http.get(f"https://api.example.com/weather/{city}") as resp:
                payload = await resp.json()
        await context.reply(f"{city}: {payload['summary']}")
```

## Offloading CPU Work

```python
import asyncio

def expensive_calculation(data: bytes) -> str:
    ...

async def handle(self, context: Context) -> None:
    result = await asyncio.to_thread(expensive_calculation, context.message.attachments[0].data)
    await context.reply(result)
```

## Middleware

- Implement reusable cross-cutting logic as middleware (`SignalClient.use(middleware)`), e.g., authentication, metrics tagging, tracing.
- Middleware signature: `async def middleware(context, call_next)`.

## Testing Tips

- Use pytest-asyncio fixtures and the provided test helpers under `tests/services` to simulate messages.
- Ensure your command yields control (e.g., `await asyncio.sleep(0)` in loops) when writing long-running tasks.

Refer to the [Quickstart](../quickstart.md) for a complete example and [Observability](../observability.md) for metrics instrumentation patterns.

---

**Next up:** Review runtime internals in the [Feature Tour](../feature-tour.md) or harden operations with the [Operations](../operations.md) runbooks.
