"""CLI entrypoints for Signal client helpers."""

from __future__ import annotations

import argparse
import asyncio
import json

from signal_client.app.application import Application
from signal_client.core.config import Settings


async def _inspect_dlq() -> None:
    """Asynchronously inspects the Dead Letter Queue (DLQ).

    Initializes the application, retrieves messages from the DLQ if configured,
    prints them as JSON, and then shuts down the application.
    Raises RuntimeError if the DLQ is not configured.
    """
    settings = Settings.from_sources()
    app = Application(settings)
    await app.initialize()
    if app.dead_letter_queue is None:
        message = "Dead Letter Queue is not configured."
        raise RuntimeError(message)

    messages = await app.dead_letter_queue.inspect()
    if not messages:
        print("Dead Letter Queue is empty.")
    else:
        print(json.dumps(messages, indent=2))
    await app.shutdown()


def inspect_dlq() -> None:
    """Inspect the Dead Letter Queue synchronously.

    This function provides a synchronous wrapper around the asynchronous
    `_inspect_dlq` function, making it test-friendly and callable from
    synchronous contexts.
    """
    asyncio.run(_inspect_dlq())


def main() -> None:
    """Main entry point for the Signal CLI.

    Parses command-line arguments and dispatches to the appropriate
    sub-command, such as inspecting the Dead Letter Queue.
    """
    parser = argparse.ArgumentParser(prog="signal-client")
    subparsers = parser.add_subparsers(dest="command")

    dlq_parser = subparsers.add_parser("dlq", help="Dead Letter Queue operations")
    dlq_subparsers = dlq_parser.add_subparsers(dest="dlq_command")
    dlq_subparsers.add_parser("inspect", help="Inspect DLQ contents")

    args = parser.parse_args()
    if args.command == "dlq" and args.dlq_command == "inspect":
        asyncio.run(_inspect_dlq())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
