# API Reference

Complete reference for Signal Client classes, methods, and configuration options with full method signatures, parameters, return values, and error handling.

## Core Classes

### `SignalClient`

The main runtime class that manages commands, workers, and the message processing loop.

```python
from signal_client.bot import SignalClient

# Initialize with default configuration
client = SignalClient()

# Or with custom configuration
client = SignalClient(config_path="/path/to/config.toml")
```

#### Constructor

```python
SignalClient(config_path: str | None = None) -> SignalClient
```

**Parameters:**
- `config_path` (optional): Path to TOML configuration file. Defaults to `~/.config/signal-client/config.toml`

**Raises:**
- `ConfigurationError`: If configuration is invalid or required settings are missing
- `FileNotFoundError`: If specified config file doesn't exist

#### Methods

##### `register(command: Command) -> None`

Register a command with the client.

```python
from signal_client.command import Command

ping_command = Command(triggers=["ping"])
client.register(ping_command)
```

**Parameters:**
- `command`: A `Command` instance with attached handler

**Raises:**
- `ValueError`: If command has no handler attached
- `DuplicateCommandError`: If a command with the same triggers is already registered

##### `async start() -> None`

Start the message processing loop. This method runs indefinitely until stopped.

```python
import asyncio

async def main():
    await client.start()

asyncio.run(main())
```

**Raises:**
- `ConnectionError`: If unable to connect to signal-cli REST API
- `AuthenticationError`: If Signal device is not properly linked
- `ConfigurationError`: If required configuration is missing

##### `async stop() -> None`

Gracefully stop the client, finishing current message processing.

```python
await client.stop()
```

**Note:** This method waits for all active message handlers to complete before stopping.

---

### `Context`

Provides access to the incoming message and methods for sending replies, reactions, and other Signal operations.

```python
from signal_client.context import Context
from signal_client.infrastructure.schemas.requests import SendMessageRequest

async def handler(context: Context) -> None:
    # Access the incoming message
    message = context.message
    
    # Send a reply
    response = SendMessageRequest(message="Hello!", recipients=[])
    await context.reply(response)
```

#### Properties

##### `message: Message`

The incoming message that triggered the command.

```python
# Access message properties
sender = context.message.source          # Phone number of sender
text = context.message.message          # Message text content
timestamp = context.message.timestamp   # Unix timestamp
group_info = context.message.group      # Group info (if group message)
attachments = context.message.attachments  # List of attachments
```

#### Methods

##### `async send(request: SendMessageRequest) -> None`

Send a message to specified recipients.

```python
from signal_client.infrastructure.schemas.requests import SendMessageRequest

request = SendMessageRequest(
    message="Hello world!",
    recipients=["+1234567890", "+0987654321"],
    mentions=[{"start": 0, "length": 5, "number": "+1234567890"}],  # Optional
    base64_attachments=["base64encodedimage..."],  # Optional
    view_once=False  # Optional
)
await context.send(request)
```

**Parameters:**
- `request`: `SendMessageRequest` object with message details

**SendMessageRequest Fields:**
- `message` (str): The message text to send
- `recipients` (list[str]): List of phone numbers to send to. Empty list sends to message sender.
- `number` (str, optional): Sender phone number. Auto-filled if not provided.
- `base64_attachments` (list[str], optional): Base64-encoded attachments
- `mentions` (list[dict], optional): List of mentions with start, length, and number
- `view_once` (bool, optional): Whether message should disappear after viewing
- `quote_author` (str, optional): Phone number of quoted message author
- `quote_message` (str, optional): Text of quoted message
- `quote_timestamp` (int, optional): Timestamp of quoted message
- `preview` (LinkPreview, optional): Link preview information

**Raises:**
- `MessageSendError`: If message fails to send
- `ValidationError`: If request parameters are invalid
- `RateLimitError`: If sending too many messages too quickly

##### `async reply(request: SendMessageRequest) -> None`

Reply to the incoming message, automatically quoting it.

```python
response = SendMessageRequest(
    message="Thanks for your message!",
    recipients=[]  # Empty list replies to sender
)
await context.reply(response)
```

**Parameters:**
- `request`: `SendMessageRequest` object. Quote fields are automatically populated.

**Note:** This method automatically sets `quote_author`, `quote_message`, and `quote_timestamp` from the incoming message.

**Raises:**
- Same exceptions as `send()`

##### `async react(emoji: str) -> None`

Add a reaction emoji to the incoming message.

```python
await context.react("👍")  # Thumbs up
await context.react("❤️")   # Heart
await context.react("😂")   # Laughing
```

**Parameters:**
- `emoji`: Unicode emoji string to react with

**Raises:**
- `ReactionError`: If reaction fails to send
- `ValueError`: If emoji is invalid or empty

##### `async remove_reaction() -> None`

Remove your reaction from the incoming message (if you previously reacted).

```python
await context.remove_reaction()
```

**Note:** Only removes reactions you previously added. Does nothing if you haven't reacted.

**Raises:**
- `ReactionError`: If reaction removal fails

#### Client Access Properties

The `Context` object provides direct access to all Signal Client API endpoints:

```python
# Access different API clients
await context.accounts.get_account_info()
await context.contacts.list_contacts()
await context.groups.list_groups()
await context.messages.get_message_history("+1234567890")
await context.profiles.get_profile("+1234567890")
```

**Available Clients:**
- `accounts`: Account management operations
- `attachments`: File attachment handling
- `contacts`: Contact management
- `devices`: Linked device management
- `general`: General Signal operations
- `groups`: Group management
- `identities`: Identity key management
- `messages`: Message operations
- `profiles`: Profile management
- `reactions`: Reaction management
- `receipts`: Read receipt handling
- `search`: Message search
- `sticker_packs`: Sticker pack management

---

### `Command`

Represents a command that can be triggered by incoming messages.

```python
from signal_client.command import Command
import re

# Simple text triggers
command = Command(triggers=["hello", "hi"])

# Regular expression triggers
command = Command(triggers=[re.compile(r"weather\s+(.+)")])

# With metadata
command = Command(
    triggers=["help"],
    whitelisted=["+1234567890"],  # Only these numbers can use this command
    case_sensitive=True,
    metadata=CommandMetadata(
        name="help",
        description="Show help information",
        usage="help [command]"
    )
)
```

#### Constructor

```python
Command(
    triggers: list[str | re.Pattern],
    whitelisted: list[str] | None = None,
    *,
    case_sensitive: bool = False,
    metadata: CommandMetadata | None = None
) -> Command
```

**Parameters:**
- `triggers`: List of strings or regex patterns that trigger this command
- `whitelisted` (optional): List of phone numbers allowed to use this command
- `case_sensitive`: Whether trigger matching is case-sensitive
- `metadata` (optional): Command metadata for help and documentation

**Raises:**
- `ValueError`: If no triggers provided or triggers list is empty

#### Methods

##### `with_handler(handler: Callable[[Context], Awaitable[None]]) -> Command`

Attach a handler function to the command.

```python
async def my_handler(context: Context) -> None:
    response = SendMessageRequest(message="Hello!", recipients=[])
    await context.reply(response)

command = Command(triggers=["hello"])
command.with_handler(my_handler)
```

**Parameters:**
- `handler`: Async function that takes a `Context` and returns `None`

**Returns:**
- The same `Command` instance (for method chaining)

**Raises:**
- `TypeError`: If handler is not an async function

---

### `CommandMetadata`

Metadata for documenting commands.

```python
from signal_client.command import CommandMetadata

metadata = CommandMetadata(
    name="weather",
    description="Get weather information for a location",
    usage="weather <city>"
)
```

#### Fields

- `name` (str, optional): Command name for help systems
- `description` (str, optional): Human-readable description
- `usage` (str, optional): Usage example or syntax

---

## Message Schemas

### `Message`

Represents an incoming Signal message.

```python
# Access message properties
sender = message.source          # Phone number of sender
text = message.message          # Message text content
timestamp = message.timestamp   # Unix timestamp (milliseconds)
group_info = message.group      # Group info dict (if group message)
attachments = message.attachments  # List of attachment dicts
```

**Properties:**
- `source` (str): Phone number of the message sender
- `message` (str | None): Text content of the message
- `timestamp` (int): Unix timestamp in milliseconds
- `group` (dict | None): Group information if this is a group message
- `attachments` (list[dict]): List of attachment metadata
- `reaction_emoji` (str | None): Emoji if this is a reaction message

**Methods:**
- `recipient() -> str`: Returns the appropriate recipient for replies
- `is_group() -> bool`: Returns True if this is a group message

### `SendMessageRequest`

Schema for sending messages.

```python
from signal_client.infrastructure.schemas.requests import SendMessageRequest

request = SendMessageRequest(
    message="Hello world!",
    recipients=["+1234567890"],
    base64_attachments=["iVBORw0KGgoAAAANSUhEUgAA..."],  # Optional
    mentions=[{
        "start": 0,
        "length": 5,
        "number": "+1234567890"
    }],  # Optional
    view_once=True,  # Optional
    quote_author="+0987654321",  # Optional
    quote_message="Original message",  # Optional
    quote_timestamp=1234567890000  # Optional
)
```

**Required Fields:**
- `message` (str): The message text to send
- `recipients` (list[str]): List of phone numbers. Empty list = reply to sender

**Optional Fields:**
- `number` (str): Sender phone number (auto-filled by Context)
- `base64_attachments` (list[str]): Base64-encoded file attachments
- `mentions` (list[dict]): Mentions with start position, length, and phone number
- `view_once` (bool): Message disappears after viewing (default: False)
- `quote_author` (str): Phone number of quoted message author
- `quote_message` (str): Text of the message being quoted
- `quote_timestamp` (int): Timestamp of quoted message
- `preview` (LinkPreview): Link preview information

### `ReactionRequest`

Schema for sending reactions.

```python
from signal_client.infrastructure.schemas.reactions import ReactionRequest

request = ReactionRequest(
    emoji="👍",
    target_author="+1234567890",
    target_timestamp=1234567890000,
    recipient="+1234567890"  # For direct messages
    # OR
    # group="groupId123"  # For group messages
)
```

**Required Fields:**
- `emoji` (str): Unicode emoji to react with
- `target_author` (str): Phone number of message author
- `target_timestamp` (int): Timestamp of message to react to

**Conditional Fields (one required):**
- `recipient` (str): For direct message reactions
- `group` (str): For group message reactions

---

## Error Handling

### Exception Hierarchy

```python
SignalClientError                    # Base exception
├── ConfigurationError              # Configuration issues
├── ConnectionError                 # Network/API connection issues
├── AuthenticationError             # Signal device linking issues
├── MessageSendError               # Message sending failures
├── ReactionError                  # Reaction sending failures
├── RateLimitError                 # Rate limiting issues
├── ValidationError                # Input validation failures
└── DuplicateCommandError          # Command registration conflicts
```

### Error Handling Patterns

```python
from signal_client.exceptions import MessageSendError, RateLimitError
import asyncio

async def robust_handler(context: Context) -> None:
    try:
        response = SendMessageRequest(message="Hello!", recipients=[])
        await context.reply(response)
    except RateLimitError:
        # Wait and retry
        await asyncio.sleep(5)
        await context.reply(response)
    except MessageSendError as e:
        # Log error and send fallback message
        print(f"Failed to send message: {e}")
        fallback = SendMessageRequest(message="Sorry, something went wrong.", recipients=[])
        await context.reply(fallback)
```

### Common Error Scenarios

#### Device Not Linked
```python
from signal_client.exceptions import AuthenticationError

try:
    await client.start()
except AuthenticationError:
    print("Signal device not linked. Please run device linking process.")
    # Guide user through QR code linking
```

#### REST API Unavailable
```python
from signal_client.exceptions import ConnectionError

try:
    await client.start()
except ConnectionError:
    print("Cannot connect to signal-cli REST API.")
    print("Ensure Docker container is running on localhost:8080")
```

#### Invalid Configuration
```python
from signal_client.exceptions import ConfigurationError

try:
    client = SignalClient(config_path="invalid.toml")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Fix configuration and retry
```

---

## CLI Tools

The Signal Client provides several command-line utilities for debugging and operations:

### `inspect-dlq`

Inspect the contents of the Dead Letter Queue for failed messages.

```bash
# Basic usage
inspect-dlq

# Expected output (empty queue)
Dead Letter Queue is empty.

# Expected output (with failed messages)
[
  {
    "message": "Failed message content",
    "error": "Connection timeout",
    "timestamp": 1234567890000,
    "retry_count": 3
  }
]
```

**Use Cases:**
- Debug message delivery failures
- Monitor system health
- Identify patterns in failures

### `release-guard`

Run production-readiness checks before deployment.

```bash
# Run all checks
release-guard --check

# Run specific checks
release-guard --check-config
release-guard --check-connectivity
release-guard --check-dependencies
```

**Checks Performed:**
- Configuration file validity
- Signal device connectivity
- REST API bridge health
- Required dependencies
- Environment variables
- File permissions

### `audit-api`

Audit API endpoints and configurations.

```bash
# Basic audit
audit-api

# Detailed audit with security checks
audit-api --security
```

**Audit Areas:**
- REST API endpoint accessibility
- Authentication status
- Rate limit configuration
- Security settings
- API version compatibility

### `pytest-safe`

Run tests with proper cleanup for async resources.

```bash
# Run all tests
pytest-safe

# Run specific test file
pytest-safe tests/test_commands.py

# Run with coverage
pytest-safe --cov=signal_client
```

**Features:**
- Proper async resource cleanup
- Signal API mocking
- Test isolation
- Coverage reporting

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SIGNAL_CLIENT_NUMBER` | Your Signal phone number | None | Yes |
| `SIGNAL_CLIENT_REST_URL` | signal-cli REST API URL | `http://localhost:8080` | No |
| `SIGNAL_CLIENT_SECRETS_DIR` | Directory for Signal credentials | `~/.local/share/signal-api` | No |
| `SIGNAL_CLIENT_CONFIG_PATH` | Path to configuration file | `~/.config/signal-client/config.toml` | No |
| `SIGNAL_CLIENT_LOG_LEVEL` | Logging level | `INFO` | No |
| `SIGNAL_CLIENT_METRICS_PORT` | Metrics server port | `9300` | No |

### Configuration File Format

```toml
[signal_client]
phone_number = "+1234567890"
rest_url = "http://localhost:8080"
secrets_dir = "/path/to/signal/credentials"

[logging]
level = "INFO"
format = "json"  # or "text"

[metrics]
enabled = true
port = 9300
path = "/metrics"

[worker]
pool_size = 4
queue_size = 200
retry_attempts = 3
retry_delay = 5.0

[rate_limiting]
enabled = true
max_messages_per_minute = 60
burst_size = 10
```

### Configuration Validation

```python
from signal_client.config import validate_config

# Validate current configuration
try:
    config = validate_config()
    print("Configuration is valid")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

---

## Advanced Usage

### Custom Middleware

```python
from signal_client.middleware import Middleware

class AuthMiddleware(Middleware):
    async def before_command(self, context: Context) -> bool:
        """Return False to block command execution."""
        if context.message.source not in AUTHORIZED_USERS:
            response = SendMessageRequest(
                message="Unauthorized user",
                recipients=[]
            )
            await context.reply(response)
            return False
        return True
    
    async def after_command(self, context: Context) -> None:
        """Called after successful command execution."""
        print(f"Command executed by {context.message.source}")

# Register middleware
client.add_middleware(AuthMiddleware())
```

### Background Tasks

```python
import asyncio
from signal_client.scheduler import schedule_task

@schedule_task(interval=3600)  # Run every hour
async def cleanup_task():
    """Periodic cleanup task."""
    print("Running cleanup...")
    # Perform cleanup operations

# Register with client
client.add_scheduled_task(cleanup_task)
```

### Custom Error Handlers

```python
from signal_client.exceptions import SignalClientError

async def error_handler(error: SignalClientError, context: Context) -> None:
    """Handle errors gracefully."""
    error_msg = SendMessageRequest(
        message=f"An error occurred: {type(error).__name__}",
        recipients=[]
    )
    await context.reply(error_msg)

# Register error handler
client.set_error_handler(error_handler)
```

---

## Best Practices

### Command Design

```python
# ✅ Good: Clear, specific triggers
command = Command(triggers=["weather", "w"])

# ❌ Bad: Overly broad triggers
command = Command(triggers=["a", "the", "is"])

# ✅ Good: Descriptive handler names
async def get_weather_forecast(context: Context) -> None:
    pass

# ❌ Bad: Generic handler names
async def handler(context: Context) -> None:
    pass
```

### Error Handling

```python
# ✅ Good: Specific error handling
async def weather_handler(context: Context) -> None:
    try:
        weather_data = await fetch_weather()
        response = SendMessageRequest(message=weather_data, recipients=[])
        await context.reply(response)
    except WeatherAPIError:
        error_response = SendMessageRequest(
            message="Weather service unavailable. Try again later.",
            recipients=[]
        )
        await context.reply(error_response)
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in weather handler: {e}")
        raise

# ❌ Bad: Catching all exceptions silently
async def bad_handler(context: Context) -> None:
    try:
        # Some operation
        pass
    except:
        pass  # Silent failure
```

### Security

```python
# ✅ Good: Whitelist sensitive commands
admin_command = Command(
    triggers=["admin"],
    whitelisted=["+1234567890"]  # Only admin numbers
)

# ✅ Good: Validate user input
async def echo_handler(context: Context) -> None:
    message_text = context.message.message or ""
    # Sanitize input
    clean_text = message_text.strip()[:500]  # Limit length
    
    if clean_text:
        response = SendMessageRequest(message=clean_text, recipients=[])
        await context.reply(response)

# ❌ Bad: No input validation
async def unsafe_echo(context: Context) -> None:
    # Direct echo without validation
    response = SendMessageRequest(message=context.message.message, recipients=[])
    await context.reply(response)
```

### Performance

```python
# ✅ Good: Async operations
async def api_handler(context: Context) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        data = response.json()
    
    reply = SendMessageRequest(message=str(data), recipients=[])
    await context.reply(reply)

# ❌ Bad: Blocking operations
async def blocking_handler(context: Context) -> None:
    import requests
    response = requests.get("https://api.example.com/data")  # Blocks event loop
    data = response.json()
    
    reply = SendMessageRequest(message=str(data), recipients=[])
    await context.reply(reply)
```