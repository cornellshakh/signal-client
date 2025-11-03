# 👋 Python Signal Client

[![CI](https://github.com/cornellshakh/signal-client/actions/workflows/ci.yml/badge.svg)](https://github.com/cornellshakh/signal-client/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/signal-client.svg)](https://pypi.org/project/signal-client/)
[![License](https://img.shields.io/pypi/l/signal_client.svg)](https://github.com/cornellshakh/signal_client/blob/main/LICENSE)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Python library for building bots and automating interactions with the Signal messaging platform. This library provides a high-level, asynchronous API for receiving messages, processing commands, and sending replies.

It is designed to work with the [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api).

## Features

- **Command-based:** Easily define and register commands with simple triggers.
- **Asynchronous:** Built on `asyncio` for high performance.
- **Extensible:** Cleanly structured with dependency injection for easy customization.
- **High-level API:** Simple `Context` object for replying, reacting, and sending messages.

## API Coverage

This library provides **100% coverage** of the `signal-cli-rest-api`. All endpoints are implemented, ensuring that you can access the full functionality of the Signal service.

## Getting Started

### Prerequisites

Before you begin, ensure you have the `signal-cli-rest-api` service running. Follow these steps to set it up with Docker:

1.  **Run `signal-cli-rest-api` in `normal` mode:**

    This command starts the service and creates a local volume to store configuration data.

    ```bash
    docker run -p 8080:8080 \
        -v $(pwd)/signal-cli-config:/home/.local/share/signal-cli \
        -e 'MODE=normal' bbernhard/signal-cli-rest-api:latest
    ```

2.  **Link your account:**

    Open [http://127.0.0.1:8080/v1/qrcodelink?device_name=local](http://127.0.0.1:8080/v1/qrcodelink?device_name=local) in your browser to generate a QR code. In your Signal app, go to **Settings > Linked devices** and scan the code to link your account.

3.  **Restart in `json-rpc` mode:**

    Once linked, restart the container in `json-rpc` mode to begin processing messages.

    ```bash
    docker run -p 8080:8080 \
        -v $(pwd)/signal-cli-config:/home/.local/share/signal-cli \
        -e 'MODE=json-rpc' bbernhard/signal-cli-rest-api:latest
    ```

### Installation

```bash
pip install signal-client
```

### Quick Example

Here is a simple "ping-pong" bot:

```python
# main.py
import asyncio
from signal_client import SignalClient, Command, Context

# 1. Define a command
class PingCommand:
    triggers = ["!ping"]
    whitelisted = []  # Optional: Restrict to specific users/groups
    case_sensitive = False  # Optional: Make triggers case-sensitive
    async def handle(self, context: Context) -> None:
        await context.reply("Pong!")

# 2. Configure and run the client
async def main():
    CONFIG = {
        "signal_service": "http://localhost:8080",
        "phone_number": "+1234567890", # Your bot's number
    }
    client = SignalClient(CONFIG)
    client.register(PingCommand())
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())
```

## Local Development

To contribute to this project, follow these steps to set up your local development environment.

### Prerequisites

- [Poetry](https://python-poetry.org/) for dependency management.
- [pre-commit](https://pre-commit.com/) for code quality checks.

### Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/cornellshakh/signal_client.git
    cd signal_client
    ```

2.  **Install dependencies:**

    Poetry will create a virtual environment and install all the required dependencies, including development tools.

    ```bash
    poetry install
    ```

3.  **Set up pre-commit hooks:**

    This will run linting and formatting checks automatically before each commit.

    ```bash
    poetry run pre-commit install
    ```

### Running Tests

To run the test suite, use the following command:

```bash
poetry run pytest
```

## Full Documentation

For a complete guide to the library's architecture, core concepts, and a full API reference, please see our **[Comprehensive Documentation](./docs/README.md)**.
