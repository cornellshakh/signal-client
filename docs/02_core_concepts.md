# Core Concepts

This document explains the fundamental concepts in the `signal-client` library that are essential for building a bot: `Command` and `Context`.

## The `Command` Protocol

A `Command` is the basic building block of your bot's functionality. It's a piece of code that runs in response to a specific trigger from an incoming message.

- **File:** `signal_client/command.py`
- **Definition:** The `Command` is a `Protocol`, which means it defines a contract or an interface that your command classes must adhere to. It is not a class you inherit from, but rather a template you implement.

### Implementation Requirements

A valid `Command` class must have the following attributes and methods:

- `triggers: list[str | re.Pattern]`: A list of strings or compiled regular expression patterns. The `Worker` will check incoming messages against this list to see if the command should be executed.
- `whitelisted: list[str]`: An optional list of user phone numbers or group IDs. If this list is not empty, only messages from these sources will trigger the command.
- `case_sensitive: bool`: Determines whether the `triggers` should be matched in a case-sensitive manner.
- `async def handle(self, context: Context) -> None:`: This is the core logic of your command. This asynchronous method is executed when the command is triggered. It receives a `Context` object, which contains all the information about the incoming message and provides methods to respond.

### Example

```python
# in my_commands/ping.py
import re
from signal_client import Command, Context

class PingCommand:
    triggers: list[str | re.Pattern] = ["!ping"]
    whitelisted: list[str] = []
    case_sensitive: bool = False

    async def handle(self, context: Context) -> None:
        await context.reply("Pong!")
```

## The `Context` Object

The `Context` object is the bridge between your command's logic and the Signal API. It's a powerful wrapper around an incoming message that makes it easy to perform common actions.

- **File:** `signal_client/context.py`
- **Purpose:** When your command's `handle` method is called, it receives a `Context` instance. This object contains the parsed `Message` and provides a clean, high-level API for responding to it.

### Key Attributes

- `message: Message`: The parsed incoming message object, containing details like the sender (`source`), the message content (`text`), and timestamp.

### Key Methods

The `Context` object provides several convenient async methods for interacting with the chat:

- `send(text: str, ...)`: Sends a new message to a specified recipient or group.
- `reply(text: str, ...)`: Sends a message that directly quotes the original message that triggered the command.
- `react(emoji: str)`: Adds an emoji reaction to the original message.
- `remove_reaction()`: Removes a previously added reaction.
- `start_typing()`: Displays the "typing..." indicator to the user.
- `stop_typing()`: Hides the typing indicator.

By using the `Context` object, your command logic remains clean and focused on the task at hand, without needing to worry about the low-level details of constructing and sending API requests.
