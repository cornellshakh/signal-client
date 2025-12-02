"""Using REST API clients directly and managing the dead-letter queue."""

from __future__ import annotations

import argparse
import asyncio
import os

from signal_client import Context, SignalClient
from signal_client.app import Application
from signal_client.command import command
from signal_client.config import Settings
from signal_client.infrastructure.schemas.groups import CreateGroupRequest
from signal_client.infrastructure.schemas.requests import SendMessageRequest


@command("!contacts")
async def list_contacts(ctx: Context) -> None:
    me = ctx._phone_number  # Provided via ContextDependencies.
    contacts = await ctx.contacts.get_contacts(me)
    await ctx.reply(
        SendMessageRequest(
            message=f"found {len(contacts)} contacts",
            recipients=[],
        )
    )


@command("!history")
async def last_messages(ctx: Context) -> None:
    me = ctx._phone_number
    history = await ctx.messages.get_messages(me, ctx.message.source, limit=5)
    snippets = [item.get("message") for item in history if item.get("message")]
    await ctx.reply(
        SendMessageRequest(
            message="recent messages:\n" + "\n".join(snippets),
            recipients=[],
        )
    )


@command("!newgroup")
async def create_group(ctx: Context) -> None:
    me = ctx._phone_number
    members = [
        ctx.message.source,
        os.environ.get("SECONDARY_MEMBER", ctx.message.source),
    ]
    request = CreateGroupRequest(name="signal-client example", members=members)
    group = await ctx.groups.create_group(me, request)
    await ctx.reply(
        SendMessageRequest(
            message=f"created group {group.get('id', '<unknown>')}",
            recipients=[],
        )
    )


async def run_bot() -> None:
    async with SignalClient() as bot:
        bot.register(list_contacts)
        bot.register(last_messages)
        bot.register(create_group)
        await bot.start()


async def replay_dlq() -> None:
    settings = Settings.from_sources()
    app = Application(settings)
    await app.initialize()
    if app.dead_letter_queue is None:
        raise RuntimeError("DLQ not configured.")

    ready = await app.dead_letter_queue.replay()
    print(f"replayed {len(ready)} messages")
    await app.shutdown()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--replay-dlq",
        action="store_true",
        help="Process eligible messages from the dead-letter queue once.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.replay_dlq:
        asyncio.run(replay_dlq())
    else:
        asyncio.run(run_bot())
