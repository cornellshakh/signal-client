# API Reference

This document provides a detailed reference for the public API of the `signal-client` library. It covers the main classes, methods, and protocols that developers will interact with when building a bot.

---

## `SignalClient`

The main entry point for creating and running a Signal bot.

- **Source:** `signal_client/bot.py`

### `__init__(self, config: dict) -> None`

Initializes the Signal client.

- **Parameters:**
  - `config` (dict): A dictionary containing the configuration for the bot. This typically includes the Signal service URL, the bot's phone number, and any storage configurations.

### `register(self, command: Command) -> None`

Registers a new command with the bot. The `WorkerPoolManager` will use this registry to match incoming messages to the appropriate command.

- **Parameters:**
  - `command` (Command): An instance of a class that implements the `Command` protocol.

### `async def start(self) -> None`

Starts the bot. This is a long-running, asynchronous method that starts the message listener and the command processor. It will run until the application is stopped.

---

## `Command` (Protocol)

A protocol that defines the required structure for a command class.

- **Source:** `signal_client/command.py`

### Attributes

- `triggers: list[str | re.Pattern]`: **(Required)** A list of strings or compiled regex patterns that will trigger the command.
- `whitelisted: list[str]`: **(Optional)** A list of phone numbers or group IDs. If provided, only messages from these sources will trigger the command. Defaults to an empty list (no restrictions).
- `case_sensitive: bool`: **(Optional)** If `True`, trigger matching is case-sensitive. Defaults to `False`.

### `async def handle(self, context: Context) -> None`

**(Required)** The main logic of the command. This asynchronous method is called when a trigger is matched.

- **Parameters:**
  - `context` (Context): The `Context` object associated with the incoming message.

---

## `Context`

Provides a high-level API for interacting with an incoming message. An instance of this class is passed to a command's `handle` method.

- **Source:** `signal_client/context.py`

### Attributes

- `message: Message`: The underlying `Message` domain model for the incoming message.

### Methods

#### `async def send(...)`

Sends a message.

- **Parameters:**
  - `text` (str): The message content.
  - `recipients` (list[str] | None): A list of recipient phone numbers or group IDs. If `None`, it defaults to the recipient of the original message.
  - `base64_attachments` (list[str] | None): A list of base64-encoded strings representing files to attach.
  - `mentions` (list[dict] | None): A list of mention objects.
  - `view_once` (bool): If `True`, the message will be marked as view-once.

#### `async def reply(...)`

Replies to the incoming message, quoting it.

- **Parameters:**
  - `text` (str): The reply message content.
  - `base64_attachments` (list[str] | None): Attachments for the reply.
  - `mentions` (list[dict] | None): Mentions for the reply.
  - `view_once` (bool): If `True`, the reply will be view-once.

#### `async def react(self, emoji: str) -> None`

Adds an emoji reaction to the incoming message.

- **Parameters:**
  - `emoji` (str): The emoji to react with.

#### `async def remove_reaction(self) -> None`

Removes a reaction from the incoming message. This is typically used when the incoming message _is_ a reaction removal event.

#### `async def start_typing(self) -> None`

Displays a typing indicator in the chat.

#### `async def stop_typing(self) -> None`

Hides the typing indicator.

---

## Exceptions

The library provides a set of custom exceptions for handling various error conditions.

- **Source:** `signal_client/domain/exceptions.py`

- `SignalClientError`: The base exception for all library-specific errors.
- `APIError`: Raised for general API errors.
- `AuthenticationError`: Raised for authentication failures (401).
- `NotFoundError`: Raised when a requested resource is not found (404).
- `ServerError`: Raised for server-side errors (5xx).
