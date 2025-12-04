# signal-client

Python framework for building Signal bots with async primitives, structured logging, and typed API clients.

## Documentation
- Public site: https://cornellsh.github.io/signal-client/
- Local preview: `poetry run mkdocs serve`

## Quick start
```bash
poetry install
poetry run pytest
```

```python
from signal_client import SignalClient, command

bot = SignalClient()

@command("!ping")
async def ping(ctx):
    await ctx.send_text("pong")

if __name__ == "__main__":
    bot.run()
```

## Development

Enable the versioned pre-commit hook so commits run the checks defined in `.pre-commit-config.yaml`:

```bash
git config core.hooksPath .githooks
```

## Examples

Sample scripts live in `examples/`. Add a short description to `examples/README.md` when you add a new example.
