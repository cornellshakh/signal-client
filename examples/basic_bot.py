"""Minimal ping bot.

Environment:
- SIGNAL_PHONE_NUMBER
- SIGNAL_SERVICE_URL
- SIGNAL_API_URL
"""

import asyncio

from signal_client import Context, SignalClient
from signal_client.command import command
from signal_client.infrastructure.schemas.requests import SendMessageRequest


@command("!ping")
async def ping(ctx: Context) -> None:
    await ctx.reply(SendMessageRequest(message="pong", recipients=[]))


async def main() -> None:
    async with SignalClient() as bot:
        bot.register(ping)
        await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
