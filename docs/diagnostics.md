---
title: Diagnostics & Troubleshooting
summary: Quick diagnostic tools and troubleshooting steps for Signal Client bots.
order: 16
---

# Diagnostics & Troubleshooting

Quick reference for diagnosing and fixing common Signal Client issues.

## Health Check Commands

Use these commands to quickly diagnose your bot's health:

```bash
# Check overall bot status
python -c "
from signal_client.config import validate_config
try:
    config = validate_config()
    print('✅ Configuration valid')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"

# Test signal-cli REST API connectivity
curl -f http://localhost:8080/v1/about || echo "❌ REST API not responding"

# Check linked accounts
curl -s http://localhost:8080/v1/accounts | python -m json.tool

# Test message sending
curl -X POST http://localhost:8080/v2/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Test", "recipients": ["+1234567890"], "number": "+1234567890"}'
```

## Common Issues & Quick Fixes

### Bot Not Responding to Messages

**Symptoms:** Bot starts but doesn't respond to commands

**Quick Diagnosis:**
```bash
# Check if bot is receiving messages
tail -f bot.log | grep "Received message"

# Verify command registration
python -c "
from your_bot import client
print('Registered commands:', [cmd.triggers for cmd in client.commands])
"
```

**Common Causes:**
- Command triggers don't match message text exactly
- Bot not polling for new messages
- Signal device not properly linked

### Signal Device Not Linked

**Symptoms:** `HTTP 400: Device not registered`

**Quick Fix:**
```bash
# Check current accounts
curl -s http://localhost:8080/v1/accounts

# If empty, re-link device
echo "Visit: http://localhost:8080/v1/qrcodelink?device_name=my-bot"
# Scan QR code with Signal mobile app
```

### REST API Connection Failed

**Symptoms:** `ConnectionError: Cannot connect to signal-cli REST API`

**Quick Fix:**
```bash
# Check if container is running
docker ps | grep signal-api

# If not running, start it
docker run -d --name signal-api \
  -p 8080:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest

# Wait for startup
sleep 15 && curl -f http://localhost:8080/v1/about
```

### Message Sending Failures

**Symptoms:** Messages fail to send or timeout

**Quick Diagnosis:**
```bash
# Test manual message sending
curl -X POST http://localhost:8080/v2/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message",
    "recipients": ["+1234567890"],
    "number": "+1234567890"
  }' -v

# Check signal-cli logs
docker logs signal-api | tail -20
```

## Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
import os

# Set debug environment
os.environ['SIGNAL_CLIENT_LOG_LEVEL'] = 'DEBUG'

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal-client-debug.log'),
        logging.StreamHandler()
    ]
)

# Your bot code here
from signal_client.bot import SignalClient
client = SignalClient()
# ... rest of your bot
```

## Performance Monitoring

Monitor your bot's performance:

```python
import psutil
import time
from signal_client.bot import SignalClient

class MonitoredBot(SignalClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        self.message_count = 0
    
    async def handle_message(self, message):
        self.message_count += 1
        
        # Log performance metrics every 100 messages
        if self.message_count % 100 == 0:
            uptime = time.time() - self.start_time
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            
            print(f"📊 Stats: {self.message_count} messages, "
                  f"{uptime:.1f}s uptime, {memory_mb:.1f}MB memory")
        
        await super().handle_message(message)
```

## Getting Help

If you're still having issues:

1. **Check the logs** — Enable debug logging and look for error details
2. **Test components individually** — Verify signal-cli, REST API, and bot separately  
3. **Review configuration** — Double-check phone numbers, URLs, and file paths
4. **Search existing issues** — Check the [GitHub repository](https://github.com/cornellsh/signal-client) for similar problems

!!! tip "Debugging Strategy"
    Start with the simplest possible bot (just ping/pong) and add complexity gradually. This helps isolate where issues are occurring.

For comprehensive troubleshooting, see the detailed [Troubleshooting Guide](troubleshooting.md).