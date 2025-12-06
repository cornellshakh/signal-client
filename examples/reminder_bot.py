"""Schedule lightweight reminders from chat messages."""

from __future__ import annotations

import asyncio

from signal_client import Context, SignalClient, command

_REQUIRED_PARTS = 3


@command("!remind")
async def remind(ctx: Context) -> None:
    """Parse `!remind <seconds> <message>` and send the reminder later."""
    raw = ctx.message.message or ""  # (1)
    parts = raw.split(maxsplit=2)
    if len(parts) < _REQUIRED_PARTS:
        await ctx.reply_text("Usage: !remind <seconds> <message>")
        return

    try:
        delay = int(parts[1])
    except ValueError:
        await ctx.reply_text("Seconds must be an integer.")
        return

    note = parts[2].strip()
    if not note:
        await ctx.reply_text("Please provide reminder text.")
        return

    async def _send_reminder() -> None:
        await asyncio.sleep(delay)  # (2)
        await ctx.send_text(f"⏰ Reminder: {note}")  # (3)

    asyncio.create_task(_send_reminder())  # noqa: RUF006  # (4)
    await ctx.reply_text(f"Reminder scheduled in {delay} seconds.")


async def main() -> None:
    """Run the reminder bot."""
    bot = SignalClient()  # (5)
    bot.register(remind)
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
