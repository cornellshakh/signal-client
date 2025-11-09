---
title: Running Your Bot
summary: Best practices for deploying and maintaining Signal bots in development and production.
order: 14
---

# Running Your Bot

Practical guidance for deploying and maintaining your Signal bot, from development to production.

## Development Setup

### Local Development

Run your bot locally for development and testing:

```python
# dev_bot.py
import asyncio
import logging
from signal_client.bot import SignalClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

async def main():
    client = SignalClient()
    
    # Add your commands here
    # ...
    
    print("🤖 Starting bot in development mode...")
    await client.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### Development Environment

```bash
# Set development environment variables
export SIGNAL_CLIENT_LOG_LEVEL=DEBUG
export SIGNAL_CLIENT_REST_API_URL=http://localhost:8080

# Run with auto-reload for development
python -m watchdog --patterns="*.py" --recursive --auto-restart python dev_bot.py
```

### Testing Commands

Test your commands manually before deployment:

```bash
# Send test message via curl
curl -X POST http://localhost:8080/v2/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "!test",
    "recipients": ["+1234567890"],
    "number": "+1234567890"
  }'

# Check bot logs
tail -f bot.log | grep "Command executed"
```

## Production Deployment

### Process Management

Use a process manager to keep your bot running:

#### Using systemd (Linux)

```ini
# /etc/systemd/system/signal-bot.service
[Unit]
Description=Signal Bot
After=network.target

[Service]
Type=simple
User=signalbot
WorkingDirectory=/home/signalbot/bot
ExecStart=/home/signalbot/bot/venv/bin/python bot.py
Restart=always
RestartSec=10
Environment=SIGNAL_CLIENT_LOG_LEVEL=INFO
Environment=SIGNAL_CLIENT_REST_API_URL=http://localhost:8080

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start the service
sudo systemctl enable signal-bot
sudo systemctl start signal-bot

# Check status
sudo systemctl status signal-bot

# View logs
sudo journalctl -u signal-bot -f
```

#### Using Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy bot code
COPY . .

# Run bot
CMD ["python", "bot.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  signal-api:
    image: bbernhard/signal-cli-rest-api:latest
    ports:
      - "8080:8080"
    volumes:
      - signal-data:/home/.local/share/signal-cli
    restart: unless-stopped

  signal-bot:
    build: .
    depends_on:
      - signal-api
    environment:
      - SIGNAL_CLIENT_REST_API_URL=http://signal-api:8080
      - SIGNAL_CLIENT_LOG_LEVEL=INFO
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

volumes:
  signal-data:
```

```bash
# Deploy with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f signal-bot

# Update bot
docker-compose build signal-bot
docker-compose up -d signal-bot
```

### Environment Configuration

Organize configuration for different environments:

```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    log_level: str = "INFO"
    rest_api_url: str = "http://localhost:8080"
    phone_number: str = ""
    
    @classmethod
    def from_env(cls):
        return cls(
            log_level=os.getenv("SIGNAL_CLIENT_LOG_LEVEL", "INFO"),
            rest_api_url=os.getenv("SIGNAL_CLIENT_REST_API_URL", "http://localhost:8080"),
            phone_number=os.getenv("SIGNAL_PHONE_NUMBER", ""),
        )

# bot.py
config = Config.from_env()
```

## Maintenance Tasks

### Regular Maintenance

Perform these tasks regularly to keep your bot healthy:

```bash
#!/bin/bash
# maintenance.sh - Run weekly

echo "🔧 Starting bot maintenance..."

# Rotate logs
if [ -f bot.log ]; then
    mv bot.log "bot.log.$(date +%Y%m%d)"
    gzip "bot.log.$(date +%Y%m%d)"
    
    # Keep only last 4 weeks of logs
    find . -name "bot.log.*.gz" -mtime +28 -delete
fi

# Check disk space
df -h | grep -E "(/$|/home)" | awk '$5 > 80 {print "⚠️  Disk usage high: " $0}'

# Update signal-cli container
docker pull bbernhard/signal-cli-rest-api:latest
docker-compose up -d signal-api

# Restart bot to clear memory
docker-compose restart signal-bot

echo "✅ Maintenance complete"
```

### Backup Important Data

```bash
#!/bin/bash
# backup.sh - Run daily

BACKUP_DIR="/backups/signal-bot/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup signal-cli data (device keys, etc.)
docker run --rm -v signal-data:/data -v "$BACKUP_DIR":/backup \
  alpine tar czf /backup/signal-data.tar.gz -C /data .

# Backup bot configuration
cp config.toml "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"

# Backup logs
cp bot.log "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Backup saved to $BACKUP_DIR"
```

## Troubleshooting Common Issues

### Bot Stops Responding

**Quick Diagnosis:**
```bash
# Check if bot process is running
ps aux | grep python | grep bot

# Check system resources
free -h
df -h

# Check signal-api connectivity
curl -f http://localhost:8080/v1/about
```

**Common Solutions:**
- Restart the bot process
- Check available memory and disk space
- Verify signal-cli container is running
- Check network connectivity

### Signal Device Unlinked

**Symptoms:** HTTP 400 errors, "Device not registered"

**Solution:**
```bash
# Check linked devices
curl -s http://localhost:8080/v1/accounts

# If empty, re-link device
echo "Visit: http://localhost:8080/v1/qrcodelink?device_name=my-bot"
# Scan QR code with Signal mobile app

# Restart bot after linking
sudo systemctl restart signal-bot
```

### High Memory Usage

**Monitor memory usage:**
```python
import psutil
import logging

def log_memory_usage():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logging.info(f"Memory usage: {memory_mb:.1f} MB")

# Call periodically in your bot
```

**Solutions:**
- Restart bot periodically (daily/weekly)
- Optimize command handlers to avoid memory leaks
- Increase server memory if needed

## Scaling Considerations

### Single Bot Limits

A single Signal bot can typically handle:
- **Personal use:** Unlimited (within Signal's rate limits)
- **Small groups:** 10-50 active users
- **Medium groups:** 100-200 users with moderate activity

### When to Scale

Consider multiple bots when you have:
- Multiple distinct use cases
- High message volume (>1000 messages/day)
- Need for redundancy
- Different phone numbers for different purposes

### Simple Load Balancing

```python
# Simple round-robin for multiple bots
import random
from typing import List

class BotPool:
    def __init__(self, bots: List[SignalClient]):
        self.bots = bots
        self.current = 0
    
    def get_bot(self) -> SignalClient:
        bot = self.bots[self.current]
        self.current = (self.current + 1) % len(self.bots)
        return bot
    
    async def send_message(self, message: str, recipient: str):
        bot = self.get_bot()
        await bot.send_message(message, recipient)
```

## Security Best Practices

### Secure Configuration

```bash
# Use environment files for secrets
echo "SIGNAL_PHONE_NUMBER=+1234567890" > .env
chmod 600 .env

# Never commit secrets to git
echo ".env" >> .gitignore
```

### Access Control

```python
# Restrict bot access to specific users/groups
ALLOWED_USERS = ["+1234567890", "+0987654321"]
ALLOWED_GROUPS = ["group-id-1", "group-id-2"]

async def check_access(context: Context) -> bool:
    user = context.message.source
    group = context.message.group_id
    
    if user in ALLOWED_USERS:
        return True
    
    if group and group in ALLOWED_GROUPS:
        return True
    
    await context.reply("❌ Access denied")
    return False

# Use in command handlers
async def admin_command(context: Context):
    if not await check_access(context):
        return
    
    # Command logic here
```

### Regular Updates

```bash
# Update dependencies regularly
pip list --outdated
pip install --upgrade signal-client

# Update signal-cli container
docker pull bbernhard/signal-cli-rest-api:latest
docker-compose up -d signal-api
```

!!! tip "Start Simple"
    Begin with a simple deployment and add complexity as needed. Most personal and small group bots don't need sophisticated infrastructure.

For detailed troubleshooting when issues occur, see the [Diagnostics Guide](diagnostics.md).