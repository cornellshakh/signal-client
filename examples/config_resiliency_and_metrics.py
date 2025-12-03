"""Configuration overrides, resiliency knobs, and Prometheus metrics."""

from __future__ import annotations

import asyncio
import os

from signal_client import Context, SignalClient
from signal_client.command import command
from signal_client.metrics_server import start_metrics_server

# Override defaults without touching environment variables for secrets.
CONFIG: dict[str, object] = {
    # Backpressure and worker sizing.
    "queue_size": 200,
    "queue_put_timeout": 0.25,
    "queue_drop_oldest_on_timeout": False,  # fail fast instead of dropping.
    "worker_pool_size": 8,
    # API resiliency.
    "api_retries": 5,
    "api_backoff_factor": 0.75,
    "api_timeout": 20,
    "rate_limit": 20,
    "rate_limit_period": 1,
    "circuit_breaker_failure_threshold": 3,
    "circuit_breaker_reset_timeout": 10,
    # Storage swap (requires Redis reachable at provided host/port).
    "storage_type": "redis",
    "redis_host": os.environ.get("REDIS_HOST", "localhost"),
    "redis_port": int(os.environ.get("REDIS_PORT", "6379")),
}


@command("!settings")
async def settings_echo(ctx: Context) -> None:
    await ctx.reply_text(
        "Custom settings active: "
        f"workers={CONFIG['worker_pool_size']}, "
        f"queue={CONFIG['queue_size']}, "
        f"retries={CONFIG['api_retries']}"
    )


async def main() -> None:
    # Expose Prometheus metrics at http://127.0.0.1:9000/
    start_metrics_server(port=9000, addr="0.0.0.0")

    async with SignalClient(config=CONFIG) as bot:
        bot.register(settings_echo)
        await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
