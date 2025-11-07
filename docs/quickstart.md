# Quickstart

!!! info "Who should read this"
    Follow this guide if you want to stand up Signal Client locally, link it to `signal-cli-rest-api`, and verify the runtime end-to-end.

This guide walks you through linking `signal-cli-rest-api`, installing Signal Client, and deploying a simple command with production-aware defaults.

## 1. Launch `signal-cli-rest-api`

```bash
mkdir -p signal-cli-config

docker run -p 8080:8080 \
  -v "$(pwd)/signal-cli-config:/home/.local/share/signal-cli" \
  -e MODE=normal bbernhard/signal-cli-rest-api:latest
```

Link your Signal account via `http://127.0.0.1:8080/v1/qrcodelink?device_name=signal-client`.

Restart the container in JSON-RPC mode after linking:

```bash
docker run -p 8080:8080 \
  -v "$(pwd)/signal-cli-config:/home/.local/share/signal-cli" \
  -e MODE=json-rpc bbernhard/signal-cli-rest-api:latest
```

## 2. Install Signal Client & Verify Compatibility

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install signal-client
python -m signal_client.compatibility
```

The compatibility guard exits non-zero when critical dependencies fall outside the supported matrix (dependency-injector, structlog, pydantic).

## 3. Scaffold Your Project

```bash
mkdir dad-joke-bot
cd dad-joke-bot
poetry init --name dad-joke-bot --dependency signal-client --no-interaction
poetry install
```

Create `.env` (optional) to store configuration:

```env
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_SERVICE=http://localhost:8080
```

## 4. Implement a Command

```python
# commands/joke.py
import random
from signal_client import Command, Context

JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "What do you call a fake noodle? An impasta!",
    "Did you hear about the claustrophobic astronaut? He just needed a little space.",
]

class JokeCommand:
    triggers = ["!joke", "!dad"]
    case_sensitive = False

    async def handle(self, context: Context) -> None:
        await context.reply(random.choice(JOKES))
        await context.react("😂")
```

## 5. Wire Signal Client

```python
# main.py
import asyncio
import os
from signal_client import SignalClient
from commands.joke import JokeCommand

async def main() -> None:
    settings = {
        "signal_service": os.environ["SIGNAL_SERVICE"],
        "phone_number": os.environ["SIGNAL_PHONE_NUMBER"],
        "worker_pool_size": 4,
        "message_queue_maxsize": 200,
    }

    client = SignalClient(settings)
    client.register(JokeCommand())

    async with client:
        await client.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## 6. Observe Metrics & Logs

Expose the Prometheus endpoint in your host app:

```python
from prometheus_client import start_http_server

start_http_server(9102)
```

- Visit `http://localhost:9102/metrics` to confirm `MESSAGE_QUEUE_DEPTH`, `MESSAGE_QUEUE_LATENCY`, and `COMMAND_INVOCATIONS`.
- Structured logs include worker IDs, command names, queue latency, and DLQ actions.

## 7. Run & Test

```bash
SIGNAL_PHONE_NUMBER=+1234567890 SIGNAL_SERVICE=http://localhost:8080 poetry run python main.py
```

Send `!joke` from a different Signal device—your bot replies instantly.

Run the full test suite whenever you iterate:

```bash
poetry run pytest-safe
```

Ready to go deeper? Explore [Architecture](./architecture.md) to understand the worker pipeline or [Operations](./operations.md) to prepare for production incidents.

---

**Next up:** Review the [Feature Tour](./feature-tour.md) for a visual map of the services or jump ahead to [Configuration](./configuration.md) to tune the runtime.
