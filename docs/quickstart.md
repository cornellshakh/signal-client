# Quickstart Guide

Build your first Signal bot in under 10 minutes! This guide walks you through setting up Signal Client, linking a device, and creating a simple bot that responds to messages.

!!! tip "What you'll build"
    By the end of this guide, you'll have a working Signal bot that responds to "ping" with "pong" and can echo messages back to you. Perfect for testing and as a foundation for more complex bots.

## Prerequisites

Before we start, make sure you have:

!!! note "Required"
    - **Signal mobile app** with an active account
    - **Python 3.9+** ([download here](https://python.org/downloads/) if needed)
    - **Docker** installed and running ([get Docker here](https://docs.docker.com/get-docker/))
    - **A phone number** for your bot (can be the same as your main Signal account)

!!! warning "Important: Phone Number Usage"
    Your bot will use a Signal account linked to a phone number. You can either:
    
    - Use your existing Signal number (bot messages will appear to come from you)
    - Get a separate number for your bot (recommended for group bots)
    
    The bot won't interfere with your normal Signal usage.

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
    You should see "Signal Client installed successfully" printed to your terminal. If you get an error, make sure you're using Python 3.9+ and try again.

[=25% "Environment ready"]

## Step 2: Set up signal-cli REST API Bridge

Signal Client communicates with Signal's servers through the `signal-cli-rest-api` bridge. This REST API provides HTTP endpoints for Signal operations, allowing your Python bot to send and receive messages without dealing with Signal's native protocol directly.

### Start the REST API Bridge

```bash
# Create directory for Signal credentials and state
mkdir -p "$HOME/.local/share/signal-api"

# Start the signal-cli-rest-api container
docker run -d \
  --name signal-api \
  -p 8080:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  -e MODE=native \
  bbernhard/signal-cli-rest-api:latest
```

!!! info "Container configuration"
    - **Volume mount**: Maps local credential storage to container's signal-cli directory
    - **Port mapping**: Exposes REST API on `localhost:8080`
    - **Native mode**: Uses GraalVM native binary for better performance
    - **Detached mode**: Runs container in background

### Verify the REST API is Running

```bash
# Check container status
docker ps | grep signal-api

# Test API endpoint availability
curl -f http://localhost:8080/v1/about || echo "API not ready yet, wait 10 seconds and try again"
```

!!! tip "Expected responses"
    - `docker ps` should show a running container named `signal-api`
    - `curl` should return JSON response with API version information

!!! warning "REST API troubleshooting"
    If the API isn't responding, try these debugging steps:
    
    ```bash
    # Check container status
    docker ps | grep signal-api
    
    # Inspect container logs for errors
    docker logs signal-api
    
    # Restart the REST API container
    docker restart signal-api
    
    # Wait for startup and test endpoint
    sleep 15 && curl http://localhost:8080/v1/about
    ```
    
    **Common issues:**
    - **Docker daemon not running**: Start Docker Desktop or systemd service
    - **Port 8080 conflict**: Stop other services using port 8080 or change port mapping
    - **Container startup failure**: Check Docker logs for specific error messages
    - **Network connectivity**: Verify Docker networking and firewall settings

[=50% "Bridge running"]

## Step 3: Link Your Signal Device

Now we need to register your Signal account with the REST API. This process links your phone number to the signal-cli instance, similar to linking Signal Desktop.

### Generate QR Code for Device Linking

1. **Request QR code from the API:**
   ```
   http://localhost:8080/v1/qrcodelink?device_name=signal-client-bot
   ```
   
   Open this URL in your browser to display the QR code.

2. **Link the device using your Signal mobile app:**
   - Open Signal app on your phone
   - Navigate to **Settings** → **Linked devices** 
   - Tap the **"+"** button (Add device)
   - Scan the QR code from your browser
   - Assign a device name like "Signal Client Bot"

!!! tip "QR code endpoint not responding?"
    If you see an HTTP error instead of a QR code, verify the REST API is running (check Step 2). The endpoint should return an HTML page with an embedded QR code image.

### Verify Device Registration

```bash
# Query registered accounts via REST API
curl -s http://localhost:8080/v1/accounts | jq '.'

# You should see your phone number in the JSON response
# If jq is not installed: curl -s http://localhost:8080/v1/accounts
```

!!! success "✅ Checkpoint 2: Device Linked"
    The API should return JSON array containing your phone number. An empty array `[]` indicates linking failed.

!!! warning "Protect Signal credentials"
    The directory `$HOME/.local/share/signal-api` now contains your Signal identity keys and cryptographic state. Secure this directory:
    
    ```bash
    # Restrict directory permissions
    chmod 700 "$HOME/.local/share/signal-api"
    ```
    
    **Never commit these credentials to version control or share them!**

[=75% "Device linked"]{: .success}

## Step 4: Create Your First Bot

Time for the fun part! Let's create a simple bot that responds to messages. This bot will:

- Respond to "ping" with "pong" 
- Echo back anything you say after "echo"
- Show you how to handle different types of messages

### Create the Bot Script

Create a new file called `my_first_bot.py` and copy this code:

```python
import asyncio
from signal_client.bot import SignalClient
from signal_client.context import Context
from signal_client.command import Command
from signal_client.infrastructure.schemas.requests import SendMessageRequest

async def main():
    """Main bot function - this is where the magic happens!"""
    # Initialize the Signal Client (it reads config from environment variables)
    client = SignalClient()
    
    # Create a ping command that responds to "ping" or "hello"
    ping_command = Command(triggers=["ping", "hello"])
    
    async def ping_handler(context: Context) -> None:
        """This function runs when someone sends 'ping' or 'hello'"""
        response = SendMessageRequest(
            message="🤖 Pong! Your bot is working! 👋",
            recipients=[]  # Empty list = reply to whoever sent the message
        )
        await context.reply(response)
    
    # Connect the handler to the command
    ping_command.with_handler(ping_handler)
    client.register(ping_command)
    
    # Create an echo command that repeats what you say
    echo_command = Command(triggers=["echo"])
    
    async def echo_handler(context: Context) -> None:
        """This function echoes back whatever comes after 'echo'"""
        message_text = context.message.message or ""
        # Remove the "echo" part and get the rest
        echo_text = message_text.replace("echo", "", 1).strip()
        
        if echo_text:
            response = SendMessageRequest(
                message=f"🔄 You said: {echo_text}",
                recipients=[]
            )
        else:
            response = SendMessageRequest(
                message="🤔 Echo what? Try: echo Hello world!",
                recipients=[]
            )
        
        await context.reply(response)
    
    # Register the echo command
    echo_command.with_handler(echo_handler)
    client.register(echo_command)
    
    # Start the bot!
    print("🚀 Starting your Signal bot...")
    print("📱 Send 'ping' or 'echo Hello' to test it")
    print("🛑 Press Ctrl+C to stop")
    
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())
```

!!! info "How this works"
    - **Commands** define what messages trigger your bot (like "ping" or "echo")
    - **Handlers** are functions that run when a command is triggered
    - **Context** gives you access to the incoming message and ways to respond
    - **SendMessageRequest** is how you send messages back

### Configure Environment Variables

Configure the Signal Client with your phone number and REST API endpoint:

/// tab | Linux/Mac
```bash
# Set your Signal phone number (the one registered with signal-cli)
export SIGNAL_CLIENT_NUMBER="+1234567890"  # ⚠️ CHANGE THIS

# Set the REST API base URL
export SIGNAL_CLIENT_REST_URL="http://localhost:8080"
```
///

/// tab | Windows (PowerShell)
```powershell
# Set your Signal phone number (the one registered with signal-cli)
$env:SIGNAL_CLIENT_NUMBER="+1234567890"  # ⚠️ CHANGE THIS

# Set the REST API base URL
$env:SIGNAL_CLIENT_REST_URL="http://localhost:8080"
```
///

/// tab | Windows (Command Prompt)
```cmd
# Set your Signal phone number (the one registered with signal-cli)
set SIGNAL_CLIENT_NUMBER=+1234567890

# Set the REST API base URL
set SIGNAL_CLIENT_REST_URL=http://localhost:8080
```
///

!!! warning "Phone number format"
    Use E.164 international format (e.g., `+1234567890`) - the same number you registered with the REST API in Step 3.

### Run Your Bot

Now for the moment of truth! Let's start your bot:

```bash
# Make sure your virtual environment is activated (if you used one)
source signal-bot-env/bin/activate  # Skip this if you didn't use venv

# Run the bot
python my_first_bot.py
```

You should see:
```
🚀 Starting your Signal bot...
📱 Send 'ping' or 'echo Hello' to test it
🛑 Press Ctrl+C to stop
```

### Test Your Bot

Time to see if it works! You can test your bot in a few ways:

!!! tip "Testing options"
    - **From another phone**: Have someone text your Signal number
    - **From Signal Desktop**: Message yourself if you have Signal Desktop installed
    - **From another Signal account**: If you have a second Signal account

**Try these commands:**

1. Send: `ping` → Bot should reply: "🤖 Pong! Your bot is working! 👋"
2. Send: `hello` → Same response (both trigger the same command)
3. Send: `echo Hello world!` → Bot should reply: "🔄 You said: Hello world!"

!!! success "✅ Checkpoint 3: Bot Working"
    Your bot should respond to messages. If it doesn't respond, check the troubleshooting section below.

!!! warning "Bot not responding?"
    If your bot isn't working, try these debugging steps:
    
    **1. Verify configuration:**
    ```bash
    # Check environment variables
    echo "Phone: $SIGNAL_CLIENT_NUMBER"
    echo "API URL: $SIGNAL_CLIENT_REST_URL"
    
    # Verify account registration with REST API
    curl -s http://localhost:8080/v1/accounts
    ```
    
    **2. Check REST API status:**
    ```bash
    # Verify container is running
    docker ps | grep signal-api
    
    # Inspect container logs for errors
    docker logs signal-api
    ```
    
    **3. Common issues:**
    - **Invalid phone number format**: Must use E.164 format (`+1234567890`)
    - **Device registration failed**: Re-run Step 3 device linking process
    - **REST API container stopped**: Restart with `docker restart signal-api`
    - **Environment variables not set**: Re-export configuration variables
    - **Python runtime errors**: Check bot console output for stack traces

[=90% "Bot responding"]{: .success}

## Step 5: You Did It! 🎉

Congratulations! You now have a working Signal bot. Let's make sure everything is solid and explore what's next.

### Quick Health Check

Run these commands to verify your setup:

```bash
# Check if any messages failed to send (should be empty)
inspect-dlq

# Run a quick system health check
release-guard --check
```

!!! success "✅ Checkpoint 4: Bot Complete"
    If both commands run without errors, your bot is ready for action! If you see errors, they'll help you identify what needs fixing.

### Save Your Configuration (Recommended)

Instead of setting environment variables every time, create a configuration file:

```bash
# Create configuration directory
mkdir -p ~/.config/signal-client

# Create configuration file (replace with your phone number)
cat > ~/.config/signal-client/config.toml << EOF
[signal_client]
phone_number = "$SIGNAL_CLIENT_NUMBER"
rest_url = "http://localhost:8080"
secrets_dir = "$HOME/.local/share/signal-api"

[logging]
level = "INFO"
format = "text"  # Use "json" for production

[metrics]
enabled = false  # Set to true if you want metrics
port = 9300
EOF
```

Now you can run your bot without setting environment variables each time!

[=100% "Bot ready!"]{: .success}

## What's Next?

🎉 **Congratulations!** You now have a working Signal bot. Here are some ideas for what to build next:

### Build Something Useful

!!! example "Popular next projects"
    - **Group moderator**: Welcome new members, delete spam, enforce rules
    - **Server monitor**: Get notified when your website goes down
    - **Family bot**: Shared shopping lists, dinner polls, event reminders  
    - **Utility commands**: Weather, calculations, quick lookups

### Learn More

- **[Use Cases & Examples](use-cases.md)** — See real bot examples you can copy and modify
- **[Writing Commands Guide](guides/writing-async-commands.md)** — Learn advanced command patterns
- **[API Reference](api-reference.md)** — Complete documentation of all methods

### Going to Production

- **[Configuration Guide](configuration.md)** — Set up proper config files and environment variables
- **[Security Best Practices](production_secrets.md)** — Keep your bot credentials safe
- **[Operations Guide](operations.md)** — Deploy and monitor your bot

### Get Help

- **[Troubleshooting](troubleshooting.md)** — Common issues and solutions
- **[GitHub Issues](https://github.com/cornellsh/signal-client/issues)** — Report bugs or ask questions
- **[Community Resources](resources.md)** — Find more help and examples

!!! tip "Start simple, then expand"
    The best bots solve specific problems for your group or personal use. Start with something simple that you actually need, then add features as you learn more about Signal Client.

---

**Happy bot building!** 🤖
