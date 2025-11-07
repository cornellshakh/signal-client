from __future__ import annotations

import pytest

from signal_client.command import command


class DummyContext:
    def __init__(self) -> None:
        self.called_with: list[str] = []


@pytest.mark.asyncio
async def test_command_metadata_defaults():
    @command("!ping")
    async def ping(ctx):
        """Return pong."""
        ctx.called_with.append("pong")

    assert ping.name == "ping"
    assert ping.description == "Return pong."
    assert ping.usage is None

    ctx = DummyContext()
    await ping(ctx)
    assert ctx.called_with == ["pong"]


@pytest.mark.asyncio
async def test_command_metadata_overrides():
    @command(
        "!echo",
        name="echo",
        description="Echoes args.",
        usage="!echo <message>",
    )
    async def echo(ctx):
        ctx.called_with.append("handled")

    assert echo.name == "echo"
    assert echo.description == "Echoes args."
    assert echo.usage == "!echo <message>"

    ctx = DummyContext()
    await echo(ctx)
    assert ctx.called_with == ["handled"]
