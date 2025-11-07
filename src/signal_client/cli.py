from __future__ import annotations

import asyncio
import json

import typer

from .container import Container


def inspect_dlq() -> None:
    """
    Inspect the contents of the Dead Letter Queue.
    """
    container = Container()
    dlq = container.services_container.dead_letter_queue()
    messages = asyncio.run(dlq.inspect())

    if not messages:
        print("Dead Letter Queue is empty.")
        return

    print(json.dumps(messages, indent=2))


def main() -> None:
    """
    Entry point for the CLI application.
    """
    app = typer.Typer()
    app.command()(inspect_dlq)
    app()


if __name__ == "__main__":
    main()
