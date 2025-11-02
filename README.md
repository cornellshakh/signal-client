# Python Signal Client

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

### Installation

```bash
pip install signal-client
```

_(Note: This is a placeholder for the actual package name if it were published.)_

### Quick Example

Here is a simple "ping-pong" bot:

```python
# main.py
import asyncio
from signal_client import SignalClient, Command, Context

# 1. Define a command
class PingCommand:
    triggers = ["!ping"]
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
