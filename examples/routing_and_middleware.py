"""Command routing, regex triggers, whitelisting, and middleware."""

from __future__ import annotations

import asyncio
import random
import re
import time
from collections.abc import Awaitable, Callable

import structlog

from signal_client import Context, SignalClient
from signal_client.command import command

log = structlog.get_logger()


async def timing_middleware(
    ctx: Context, next_callable: Callable[[Context], Awaitable[None]]
) -> None:
    started = time.perf_counter()
    await next_callable(ctx)
    elapsed_ms = (time.perf_counter() - started) * 1000
    log.info("command.timing", command=ctx.message.message, elapsed_ms=elapsed_ms)


async def blocklist_middleware(
    ctx: Context, next_callable: Callable[[Context], Awaitable[None]]
) -> None:
    # Only allow messages from contacts in a safe list.
    blocklisted = {"+19998887777"}
    if ctx.message.source in blocklisted:
        return
    await next_callable(ctx)


@command(re.compile(r"!roll\s+(\d+)d(\d+)", re.IGNORECASE))
async def dice(ctx: Context) -> None:
    match = re.search(r"!roll\s+(\d+)d(\d+)", ctx.message.message or "", re.IGNORECASE)
    if not match:
        return
    count, sides = (int(match.group(1)), int(match.group(2)))
    rolls = [random.randint(1, sides) for _ in range(count)]
    await ctx.reply_text(f"Rolled {count}d{sides}: {rolls} (total={sum(rolls)})")


@command("!ADMIN", whitelisted=["+1234567890"], case_sensitive=True)
async def admin_only(ctx: Context) -> None:
    await ctx.reply_text("admin OK")


async def main() -> None:
    async with SignalClient() as bot:
        bot.use(timing_middleware)
        bot.use(blocklist_middleware)
        bot.register(dice)
        bot.register(admin_only)
        await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
