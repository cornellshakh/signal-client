# Getting Started Tutorial: Your First Bot

This tutorial will guide you through the process of creating a simple "ping-pong" bot using the `signal-client` library. The bot will listen for messages containing `!ping` and respond with `Pong!`.

## Prerequisites

- Python 3.8+
- The `signal-client` library installed.
- Access to a running Signal service and the necessary credentials (phone number, service URL).

## Step 1: Project Structure

First, let's create a simple directory structure for our bot.

```
my-signal-bot/
├── commands/
│   ├── __init__.py
│   └── ping.py
└── main.py
```

## Step 2: Create the `PingCommand`

Inside `commands/ping.py`, we will define our command. This class will implement the `Command` protocol and contain the logic to reply to the ping.

```python
# commands/ping.py
from signal_client import Command, Context

class PingCommand:
    """A simple command that replies with Pong!"""
    triggers = ["!ping"]
    whitelisted = []
    case_sensitive = False

    async def handle(self, context: Context) -> None:
        await context.reply("Pong!")
```

- We set `triggers` to `["!ping"]` so the command runs when a message contains `!ping`.
- `case_sensitive` is `False`, so `!Ping` or `!PING` will also work.
- The `handle` method uses the `context.reply()` function to send a reply that quotes the original message.

## Step 3: Create the Main Application

Next, in `main.py`, we will write the code to initialize the `SignalClient`, register our command, and start the bot.

```python
# main.py
import asyncio
from signal_client import SignalClient
from commands.ping import PingCommand

# --- Configuration ---
# In a real application, you would load this from a file or environment variables.
CONFIG = {
    "signal_service": "http://localhost:8080",  # URL of your signal-cli-rest-api instance
    "phone_number": "+1234567890",            # The phone number of your bot
    "storage": {
        "provider": "sqlite",  # or "redis"
        "path": "signal_storage.db",
    },
}

async def main():
    """The main entry point for the bot."""
    client = SignalClient(CONFIG)
    client.register(PingCommand())

    print("Bot is starting...")
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())
```

- We import the necessary classes, including our `PingCommand`.
- We define a `CONFIG` dictionary. **Remember to replace the placeholder values with your actual configuration.**
- In the `main` function, we create an instance of `SignalClient`, register an instance of our `PingCommand`, and then `await client.start()` to begin listening for messages.

## Step 4: Run the Bot

You can now run your bot from the terminal:

```bash
python main.py
```

If everything is configured correctly, you will see the "Bot is starting..." message. Now, if you send a message containing `!ping` to your bot's phone number from another Signal account, it should instantly reply with "Pong!".

Congratulations, you've built your first Signal bot! You can now expand on this by adding more commands to the `commands/` directory and registering them in `main.py`.
