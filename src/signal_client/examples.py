from __future__ import annotations

from signal_client.command import command
from signal_client.context import Context
from signal_client.infrastructure.schemas.requests import SendMessageRequest


@command("!ping")
async def ping(context: Context) -> None:
    """Replies with 'pong'."""
    request = SendMessageRequest(message="pong", recipients=[])
    await context.send(request)


@command("!echo")
async def echo(context: Context) -> None:
    """Echoes the user's message."""
    if context.message.message:
        request = SendMessageRequest(message=context.message.message, recipients=[])
        await context.send(request)


@command("!help")
async def help_command(context: Context) -> None:
    """Lists the available commands."""
    commands = [
        "!ping - Replies with 'pong'",
        "!echo <message> - Echoes the user's message",
        "!help - Lists the available commands",
    ]
    request = SendMessageRequest(message="\n".join(commands), recipients=[])
    await context.send(request)
