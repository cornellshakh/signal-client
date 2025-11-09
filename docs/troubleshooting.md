---
title: Common Issues
summary: Quick solutions to the most common Signal bot problems.
order: 400
---

# Common Issues

Quick solutions to problems you might encounter while building your Signal bot.

## Quick Health Check

Run this command to check if everything is working:

```bash
# Test your Signal bot setup
curl -f http://localhost:8080/v1/about && echo "✅ REST API running" || echo "❌ REST API down"
curl -s http://localhost:8080/v1/accounts | grep -q "+" && echo "✅ Device linked" || echo "❌ No device linked"
```

## Most Common Problems

### 1. "Device not registered" Error

**Problem:** Your bot can't send messages and shows HTTP 400 errors.

**Quick Fix:**
```bash
# Check if device is linked
curl -s http://localhost:8080/v1/accounts

# If empty [], you need to link your device:
# 1. Visit: http://localhost:8080/v1/qrcodelink?device_name=my-bot
# 2. Scan QR code with Signal mobile app
# 3. Wait 10 seconds, then test again
```

### 2. REST API Not Responding

**Problem:** `curl: (7) Failed to connect to localhost:8080`

**Quick Fix:**
```bash
# Check if signal-cli container is running
docker ps | grep signal-cli-rest-api

# If not running, start it:
docker run -d -p 8080:8080 \
  -v signal-data:/home/.local/share/signal-cli \
  bbernhard/signal-cli-rest-api:latest

# Wait 30 seconds for startup, then test
curl http://localhost:8080/v1/about
```

### 3. Bot Not Receiving Messages

**Problem:** Your bot doesn't respond to messages sent to it.

**Check these:**
```python
# 1. Make sure your bot is listening for messages
client = SignalClient()

@client.command("!test")
async def test_command(context):
    await context.reply("Bot is working!")

# 2. Start the bot properly
await client.start()  # This line is required!
```

**Debug steps:**
```bash
# Check if messages are reaching the REST API
curl -s http://localhost:8080/v1/receive/+1234567890

# Enable debug logging in your bot
export SIGNAL_CLIENT_LOG_LEVEL=DEBUG
python your_bot.py
```

### 4. Permission Denied Errors

**Problem:** `PermissionError: [Errno 13] Permission denied`

**Quick Fix:**
```bash
# Fix signal-cli data permissions
chmod 700 ~/.local/share/signal-cli
find ~/.local/share/signal-cli -type f -exec chmod 600 {} \;

# If using Docker, check volume permissions
docker run --rm -v signal-data:/data alpine ls -la /data
```

### 5. Import Errors

**Problem:** `ModuleNotFoundError: No module named 'signal_client'`

**Quick Fix:**
```bash
# Install signal-client
pip install signal-client

# Or if using virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install signal-client
```

### 6. Messages Not Sending

**Problem:** No error, but messages don't appear in Signal app.

**Check these:**
```python
# 1. Use correct phone number format
await client.send_message("Hello!", "+1234567890")  # ✅ With country code
await client.send_message("Hello!", "1234567890")   # ❌ Missing +

# 2. Check if recipient number is correct
print(f"Sending to: {recipient}")  # Debug output

# 3. Test with your own number first
await client.send_message("Test", "+1234567890")  # Your number
```

### 7. High Memory Usage

**Problem:** Bot uses too much memory over time.

**Quick Fix:**
```python
# Add periodic restart to your bot
import asyncio
from datetime import datetime, timedelta

class BotManager:
    def __init__(self):
        self.start_time = datetime.now()
    
    async def should_restart(self):
        # Restart every 24 hours
        uptime = datetime.now() - self.start_time
        return uptime > timedelta(hours=24)
    
    async def run_with_restart(self):
        while True:
            try:
                await client.start()
            except Exception as e:
                print(f"Bot crashed: {e}")
                await asyncio.sleep(60)  # Wait before restart

# Or use systemd/Docker restart policies
```

## Environment Issues

### Docker Problems

```bash
# Common Docker fixes

# 1. Container won't start
docker logs signal-cli-rest-api

# 2. Port already in use
docker ps | grep 8080
# Kill conflicting container or use different port

# 3. Volume permission issues
docker run --rm -v signal-data:/data alpine chown -R 1000:1000 /data
```

### Python Environment

```bash
# Common Python fixes

# 1. Wrong Python version
python --version  # Should be 3.8+

# 2. Virtual environment issues
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install signal-client

# 3. Package conflicts
pip list | grep signal
pip uninstall signal-client
pip install signal-client
```

## Getting Debug Information

When asking for help, include this information:

```bash
#!/bin/bash
# debug-info.sh - Collect debug information

echo "=== System Info ==="
uname -a
python --version
docker --version

echo "=== Signal Client Info ==="
pip show signal-client
curl -s http://localhost:8080/v1/about 2>/dev/null || echo "REST API not responding"
curl -s http://localhost:8080/v1/accounts 2>/dev/null || echo "Cannot check accounts"

echo "=== File Permissions ==="
ls -la ~/.local/share/signal-cli/ 2>/dev/null || echo "No signal-cli directory"

echo "=== Docker Status ==="
docker ps | grep signal-cli-rest-api || echo "No signal-cli container running"

echo "=== Recent Logs ==="
tail -20 ~/.local/share/signal-cli/logs/signal-cli.log 2>/dev/null || echo "No logs found"
```

## Still Need Help?

1. **Check existing issues:** [GitHub Issues](https://github.com/cornellsh/signal-client/issues)
2. **Create minimal example:** Reduce your code to the smallest failing case
3. **Include debug info:** Run the debug script above
4. **Open new issue:** With all the information gathered

!!! tip "Most Problems Are Simple"
    90% of Signal bot issues are caused by:
    - Device not linked properly
    - Wrong phone number format
    - REST API not running
    - Permission problems
    
    Check these first before diving deeper!

For more detailed diagnostics, see the [Diagnostics Guide](diagnostics.md).