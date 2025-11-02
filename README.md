# Signal Client

[![PyPI version](https://img.shields.io/pypi/v/signal_client.svg)](https://pypi.org/project/signal_client/)
[![Python versions](https://img.shields.io/pypi/pyversions/signal_client.svg)](https://pypi.org/project/signal_client/)
[![License](https://img.shields.io/pypi/l/signal_client.svg)](https://github.com/cornellshakh/signal_client/blob/main/LICENSE)

## Quick Start

Get a client running by following these steps.

### 1. Start the Signal API

```bash
docker run -d --rm \
    -p 8080:8080 \
    -v $(pwd)/signal-cli-config:/home/.local/share/signal-cli \
    -e 'MODE=json-rpc' --name signal-bot-api bbernhard/signal-cli-rest-api:latest
```

### 2. Configure Your Environment

```bash
export SIGNAL_SERVICE="127.0.0.1:8080"
export PHONE_NUMBER="+YourSignalNumber" # Replace with your number
```

### 3. Run the Client

```bash
pip install signal_client && python -c "
import os, asyncio, logging
from signal_client import SignalClient, Command, Context

logging.basicConfig(level=logging.INFO)

class PingCommand(Command):
    triggers = ['!ping']
    async def handle(self, c: Context) -> None:
        await c.reply('Pong')

if __name__ == '__main__':
    bot = SignalClient({
        'signal_service': os.environ['SIGNAL_SERVICE'],
        'phone_number': os.environ['PHONE_NUMBER'],
    })
    bot.register(PingCommand())
    print('Client is starting... Press Ctrl+C to stop.')
    asyncio.run(bot.start())
"
```

## Architecture Overview

This diagram provides a high-level overview of the client's architecture.

```mermaid
graph LR
    subgraph Your World
        A[You]
    end

    subgraph The Internet
        B((Signal Network))
    end

    subgraph The Client's World
        C[SignalClient]
        D{Commands}
        E[PingCommand]
        F[Your Own Command]
    end

    A -- "!ping" --> B
    B -- Message --> C
    C -- Looks for --> D
    D -- Finds --> E
    E -- Replies "Pong" --> C
    C -- Sends --> B
    B -- "Pong" --> A

    D -- You can add --> F
```

## Usage Examples

Here are some examples for common tasks.

### Example 1: A Simple Command Handler

This is a minimal example of a client with a single command handler.

```python
# hello_client.py
import os
import asyncio
from signal_client import SignalClient, Command, Context

class HelloCommand(Command):
    triggers = ["!hello"]
    async def handle(self, c: Context) -> None:
        await c.reply(f"Hello, {c.message.sender.name}!")

if __name__ == "__main__":
    bot = SignalClient({
        "signal_service": os.environ["SIGNAL_SERVICE"],
        "phone_number": os.environ["PHONE_NUMBER"],
    })
    bot.register(HelloCommand())
    asyncio.run(bot.start())
```

### Example 2: An Echo Handler

This client will echo back the text of any message that triggers the `!echo` command.

```python
# echo_client.py
import os
import asyncio
from signal_client import SignalClient, Command, Context

class EchoCommand(Command):
    triggers = ["!echo"]
    async def handle(self, c: Context) -> None:
        await c.reply(c.message.text)

if __name__ == "__main__":
    bot = SignalClient({
        "signal_service": os.environ["SIGNAL_SERVICE"],
        "phone_number": os.environ["PHONE_NUMBER"],
    })
    bot.register(EchoCommand())
    asyncio.run(bot.start())
```

## Design Principles

This library is designed with the following principles in mind:

- **Simplicity:** The API is designed to be minimal and intuitive, allowing you to focus on your application logic rather than the library's internals.
- **Convention over configuration:** Sensible defaults are used where possible, reducing the need for boilerplate configuration.
