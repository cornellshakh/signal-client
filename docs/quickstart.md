# Quickstart

Set up Signal Client from scratch, link a Signal device, send your first message, and verify everything works in under 30 minutes.

!!! note "Prerequisites"
    - **Signal mobile app** installed with an active account
    - **Python 3.9+** installed (`python --version` to check)
    - **Docker** installed and running (`docker --version` to check)
    - **Internet access** to Signal's servers and Docker Hub
    - **Phone number** that you want to use for the bot (can be different from your main Signal account)

## Step 1: Install Signal Client

Choose your preferred Python package manager:

/// tab | `pip` (Recommended)

    :::bash
    # Create isolated environment
    python -m venv signal-bot-env
    source signal-bot-env/bin/activate  # On Windows: signal-bot-env\Scripts\activate
    
    # Install Signal Client
    pip install signal-client
    
    # Verify installation
    python -c "import signal_client; print('Signal Client installed successfully')"
///

/// tab | `uv` (Fast)

    :::bash
    # Create project with uv
    uv init signal-bot
    cd signal-bot
    uv add signal-client
    
    # Verify installation
    uv run python -c "import signal_client; print('Signal Client installed successfully')"
///

/// tab | `poetry` (Dependency Management)

    :::bash
    # Create new project
    poetry new signal-bot
    cd signal-bot
    poetry add signal-client
    
    # Verify installation
    poetry run python -c "import signal_client; print('Signal Client installed successfully')"
///

!!! success "✅ Checkpoint 1: Installation Complete"
    You should see "Signal Client installed successfully" printed to your terminal.

[=25% "Environment ready"]

## Step 2: Set up signal-cli REST API Bridge

Signal Client requires a REST API bridge to communicate with Signal's servers. We'll use the official `signal-cli-rest-api` Docker image.

### Start the REST API Bridge

```bash
# Create directory for Signal credentials (will be created if it doesn't exist)
mkdir -p "$HOME/.local/share/signal-api"

# Start the REST API bridge
docker run -d \
  --name signal-api \
  -p 8080:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  -e MODE=native \
  bbernhard/signal-cli-rest-api:latest
```

### Verify the Bridge is Running

```bash
# Check container status
docker ps | grep signal-api

# Test API endpoint
curl -f http://localhost:8080/v1/about || echo "API not ready yet, wait 10 seconds and try again"
```

!!! tip "Expected Output"
    - `docker ps` should show a running container named `signal-api`
    - `curl` should return JSON with version information, not an error

!!! warning "Troubleshooting Bridge Issues"
    If the bridge isn't responding:
    ```bash
    # Check container logs
    docker logs signal-api
    
    # Restart if needed
    docker restart signal-api
    
    # Wait 10-15 seconds for startup, then test again
    sleep 15 && curl http://localhost:8080/v1/about
    ```

[=50% "Bridge running"]

## Step 3: Link Your Signal Device

### Generate QR Code for Device Linking

1. **Open the QR code URL** in your browser:
   ```
   http://localhost:8080/v1/qrcodelink?device_name=signal-client-bot
   ```

2. **Scan the QR code** using your Signal mobile app:
   - Open Signal app → Settings → Linked devices → "+" (Add device)
   - Scan the QR code displayed in your browser
   - Give the device a name like "Signal Bot"

### Verify Device Linking

```bash
# Check if device was linked successfully
curl -s http://localhost:8080/v1/accounts | jq '.'

# You should see your phone number in the response
# If jq is not installed: curl -s http://localhost:8080/v1/accounts
```

!!! success "✅ Checkpoint 2: Device Linked"
    The API should return JSON containing your phone number. If you see an empty array `[]`, the linking failed.

!!! danger "Security Warning"
    The credentials stored in `$HOME/.local/share/signal-api` contain your Signal identity keys. Protect this directory:
    ```bash
    chmod 700 "$HOME/.local/share/signal-api"
    ```

[=75% "Device linked"]{: .success}

## Step 4: Create Your First Bot

Now let's create a simple bot that responds to messages.

### Create the Bot Script

Create a file called `my_first_bot.py`:

```python
import asyncio
import os
from signal_client.bot import SignalClient
from signal_client.context import Context
from signal_client.command import Command
from signal_client.infrastructure.schemas.requests import SendMessageRequest

# Set your phone number (the one you linked to Signal)
# Replace with your actual phone number in international format
PHONE_NUMBER = "+1234567890"  # ⚠️ CHANGE THIS TO YOUR NUMBER

async def main():
    """Main bot function."""
    # Initialize the Signal Client
    client = SignalClient()
    
    # Create a simple ping command
    ping_command = Command(triggers=["ping", "hello"])
    
    async def ping_handler(context: Context) -> None:
        """Respond to ping messages."""
        # Create a proper message request
        response = SendMessageRequest(
            message="🤖 Signal Client is online! Pong! 👋",
            recipients=[]  # Empty list means reply to sender
        )
        await context.reply(response)
    
    # Register the command handler
    ping_command.with_handler(ping_handler)
    client.register(ping_command)
    
    # Create an echo command that repeats what you say
    echo_command = Command(triggers=["echo"])
    
    async def echo_handler(context: Context) -> None:
        """Echo back the message."""
        # Get the message text after the trigger word
        message_text = context.message.message or ""
        echo_text = message_text.replace("echo", "", 1).strip()
        
        if echo_text:
            response = SendMessageRequest(
                message=f"🔄 You said: {echo_text}",
                recipients=[]
            )
            await context.reply(response)
        else:
            response = SendMessageRequest(
                message="🤔 Echo what? Try: echo Hello world!",
                recipients=[]
            )
            await context.reply(response)
    
    echo_command.with_handler(echo_handler)
    client.register(echo_command)
    
    print(f"🚀 Starting Signal Client bot for {PHONE_NUMBER}")
    print("📱 Send 'ping' or 'echo Hello' to test the bot")
    print("🛑 Press Ctrl+C to stop")
    
    # Start the bot
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Configure Environment Variables

Set the required environment variables:

```bash
# Set your Signal phone number (the one you linked)
export SIGNAL_CLIENT_NUMBER="+1234567890"  # ⚠️ CHANGE THIS

# Set the REST API URL (should match your Docker container)
export SIGNAL_CLIENT_REST_URL="http://localhost:8080"

# Optional: Set secrets directory (defaults to ~/.local/share/signal-api)
export SIGNAL_CLIENT_SECRETS_DIR="$HOME/.local/share/signal-api"
```

### Run Your Bot

```bash
# Make sure your virtual environment is activated
source signal-bot-env/bin/activate  # or your chosen environment

# Run the bot
python my_first_bot.py
```

### Test Your Bot

1. **Send a test message** to your Signal number from another device or Signal Desktop
2. **Try these commands:**
   - Send: `ping` → Bot should reply: "🤖 Signal Client is online! Pong! 👋"
   - Send: `hello` → Same response
   - Send: `echo Hello world!` → Bot should reply: "🔄 You said: Hello world!"

!!! success "✅ Checkpoint 3: Bot Working"
    Your bot should respond to messages. If it doesn't respond, check the troubleshooting section below.

!!! warning "Troubleshooting Bot Issues"
    **Bot not responding?**
    ```bash
    # Check if your phone number is correct
    curl -s http://localhost:8080/v1/accounts
    
    # Check bot logs for errors
    # Look for connection errors or authentication issues
    
    # Verify environment variables
    echo "Phone: $SIGNAL_CLIENT_NUMBER"
    echo "API URL: $SIGNAL_CLIENT_REST_URL"
    ```
    
    **Common issues:**
    - Wrong phone number format (must include country code: +1234567890)
    - Signal device not properly linked
    - REST API bridge not running
    - Firewall blocking localhost:8080

[=90% "Bot responding"]{: .success}

## Step 5: Validate Your Setup

Use the built-in CLI tools to verify everything is working correctly:

### Check Dead Letter Queue

```bash
# Inspect failed messages (should be empty for a new setup)
inspect-dlq

# Expected output: "Dead Letter Queue is empty." or JSON with failed messages
```

### Run Production Readiness Checks

```bash
# Run comprehensive system checks
release-guard --check

# This validates:
# - Signal device connectivity
# - REST API bridge health
# - Configuration completeness
# - Required dependencies
```

### Audit API Configuration

```bash
# Check API endpoints and configuration
audit-api

# This verifies:
# - REST API endpoints are accessible
# - Authentication is working
# - Rate limits are configured
```

!!! success "✅ Checkpoint 4: System Validated"
    All CLI tools should run without errors. If any fail, check the troubleshooting section.

### Create Configuration File (Optional)

For production use, create a configuration file:

```bash
# Create configuration directory
mkdir -p ~/.config/signal-client

# Create configuration file
cat > ~/.config/signal-client/config.toml << EOF
[signal_client]
phone_number = "$SIGNAL_CLIENT_NUMBER"
rest_url = "http://localhost:8080"
secrets_dir = "$HOME/.local/share/signal-api"

[logging]
level = "INFO"
format = "json"

[metrics]
enabled = true
port = 9300
EOF
```

!!! tip "Configuration Best Practices"
    - **Never commit secrets** to version control
    - Use environment variables for sensitive values
    - Keep configuration files in `~/.config/signal-client/`
    - Use different configs for development and production

[=100% "Ready for production"]{: .success}

## Next Steps

🎉 **Congratulations!** You now have a working Signal Client bot. Here's what to explore next:

### Learn More
- **[API Reference](api-reference.md)** — Complete method signatures and examples
- **[Writing Commands](guides/writing-async-commands.md)** — Advanced command patterns
- **[Configuration](configuration.md)** — Production configuration options
- **[Security Guide](production_secrets.md)** — Secure credential management

### Production Deployment
- **[Architecture](architecture.md)** — Understanding the runtime structure
- **[Operations](operations.md)** — Monitoring and maintenance
- **[Observability](observability.md)** — Metrics and logging

### Common Use Cases
- **[Feature Tour](feature-tour.md)** — Explore all capabilities
- **[Use Cases](use-cases.md)** — Real-world examples

!!! warning "Before Production"
    - Review the [Security Guide](production_secrets.md) for credential management
    - Set up proper [monitoring and alerting](observability.md)
    - Test your bot thoroughly with edge cases
    - Plan for [backup and recovery](operations.md#incident-response)

---

**Need help?** Check our [troubleshooting guide](diagnostics.md) or [open an issue](https://github.com/cornellsh/signal-client/issues) on GitHub.
