# Quickstart

Follow these steps to stand up a minimal async bot.

## 1. Install dependencies

=== "Pip"

    Install with {{ install_snippet('pip') }}.

=== "Poetry"

    Install with {{ install_snippet('poetry') }}.

## 2. Bootstrap a project

```bash
poetry install --sync
poetry run ruff check .
poetry run mypy src
```

## 3. Write an echo bot

```python exec="true" title="echo_bot.py"
import asyncio
from signal_client.bot import Bot

bot = Bot()

@bot.command("echo")
async def echo(context, message):
    """Simple echo handler"""
    await context.reply(message.text)

if __name__ == "__main__":
    asyncio.run(bot.run())
```

Use `Exec` blocks only for illustrative snippets; the codexec extension sandboxes execution.

## 4. Run tests

```bash
poetry run pytest-safe -n auto --cov=signal_client
```

Next stop: [Architecture](architecture.md) for the moving pieces.
