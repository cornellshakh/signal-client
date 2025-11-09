---
title: Security & Secrets
summary: Keep your Signal bot secure with proper credential management and security practices.
order: 301
---

# Security & Secrets

Essential security practices for protecting your Signal bot and keeping your credentials safe.

## Understanding Signal Credentials

When you link your Signal bot, important security files are created:

```bash
# Default location: ~/.local/share/signal-api/
├── data/
│   └── +1234567890/           # Your phone number
│       ├── account.json       # Account settings
│       ├── identity.json      # Identity keys (CRITICAL)
│       ├── sessions/          # Contact encryption keys
│       └── groups/            # Group data
```

!!! danger "Protect Your Identity Keys"
    The `identity.json` file contains your Signal identity keys. If lost or stolen:
    - You'll lose access to your Signal account permanently
    - Attackers could read your messages and impersonate you
    - **Always backup these files securely**

## Basic Security Setup

### Secure File Permissions

Protect your credential files from other users on your system:

```bash
# Make signal directory private
chmod 700 ~/.local/share/signal-api

# Make all files readable only by you
find ~/.local/share/signal-api -type f -exec chmod 600 {} \;

# Verify permissions (should show drwx------ for directories)
ls -la ~/.local/share/signal-api/
```

### Environment Variables

Never hardcode credentials in your code. Use environment variables:

```python
# ❌ Don't do this
phone_number = "+1234567890"

# ✅ Do this instead
import os
phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
```

Create a `.env` file for local development:

```bash
# .env (never commit this file!)
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_CLIENT_REST_API_URL=http://localhost:8080
```

```python
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import os
phone_number = os.getenv("SIGNAL_PHONE_NUMBER")
```

**Important:** Add `.env` to your `.gitignore`:

```bash
echo ".env" >> .gitignore
```

## Production Deployment

### Docker Security

Use proper security practices in Docker:

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash signalbot
USER signalbot
WORKDIR /home/signalbot

# Install dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Copy bot code
COPY --chown=signalbot:signalbot . .

# Run as non-root
CMD ["python", "bot.py"]
```

### Docker Compose with Secrets

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
    environment:
      - SIGNAL_PHONE_NUMBER=${SIGNAL_PHONE_NUMBER}
      - SIGNAL_CLIENT_REST_API_URL=http://signal-api:8080
    restart: unless-stopped
    depends_on:
      - signal-api

volumes:
  signal-data:
```

### Server Security

Basic server security for your Signal bot:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install fail2ban to prevent brute force attacks
sudo apt install fail2ban -y

# Configure firewall (allow only necessary ports)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080  # Only if signal-api needs external access
sudo ufw enable

# Create dedicated user for the bot
sudo useradd -m -s /bin/bash signalbot
sudo su - signalbot
```

## Backup & Recovery

### Backup Your Credentials

**Critical:** Always backup your Signal credentials before deploying:

```bash
#!/bin/bash
# backup-signal-credentials.sh

BACKUP_DIR="$HOME/signal-backups/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup signal-cli data
cp -r ~/.local/share/signal-api/data "$BACKUP_DIR/"

# Create encrypted archive
tar czf "$BACKUP_DIR/signal-credentials.tar.gz" -C "$BACKUP_DIR" data
rm -rf "$BACKUP_DIR/data"

# Encrypt the backup (requires gpg)
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/signal-credentials.tar.gz"
rm "$BACKUP_DIR/signal-credentials.tar.gz"

echo "✅ Backup saved to: $BACKUP_DIR/signal-credentials.tar.gz.gpg"
echo "🔐 Store this file securely and remember your passphrase!"
```

### Recovery Process

If you need to restore your credentials:

```bash
#!/bin/bash
# restore-signal-credentials.sh

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file.tar.gz.gpg>"
    exit 1
fi

# Decrypt backup
gpg --decrypt "$BACKUP_FILE" > signal-credentials.tar.gz

# Extract to signal directory
mkdir -p ~/.local/share/signal-api
tar xzf signal-credentials.tar.gz -C ~/.local/share/signal-api/

# Set proper permissions
chmod 700 ~/.local/share/signal-api
find ~/.local/share/signal-api -type f -exec chmod 600 {} \;

# Clean up
rm signal-credentials.tar.gz

echo "✅ Credentials restored. Restart your bot."
```

## Access Control

### Restrict Bot Access

Limit who can use your bot:

```python
# config.py
ALLOWED_USERS = [
    "+1234567890",  # Your number
    "+0987654321",  # Trusted friend
]

ALLOWED_GROUPS = [
    "group-id-1",   # Family group
    "group-id-2",   # Work team
]

# bot.py
from signal_client.context import Context

async def check_access(context: Context) -> bool:
    """Check if user is authorized to use the bot."""
    user = context.message.source
    group = context.message.group_id
    
    # Allow specific users
    if user in ALLOWED_USERS:
        return True
    
    # Allow users in specific groups
    if group and group in ALLOWED_GROUPS:
        return True
    
    # Deny access
    await context.reply("❌ Access denied")
    logging.warning(f"Unauthorized access attempt from {user}")
    return False

# Use in command handlers
async def admin_command(context: Context):
    if not await check_access(context):
        return
    
    # Command logic here
    await context.reply("✅ Admin command executed")
```

### Rate Limiting

Prevent abuse with simple rate limiting:

```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, user: str) -> bool:
        now = time.time()
        user_requests = self.requests[user]
        
        # Remove old requests
        user_requests[:] = [req_time for req_time in user_requests 
                           if now - req_time < self.window_seconds]
        
        # Check if under limit
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        
        return False

# Usage
rate_limiter = RateLimiter(max_requests=5, window_seconds=60)

async def rate_limited_command(context: Context):
    user = context.message.source
    
    if not rate_limiter.is_allowed(user):
        await context.reply("⏰ Rate limit exceeded. Please wait a minute.")
        return
    
    # Command logic here
```

## Monitoring & Alerts

### Security Logging

Log security-relevant events:

```python
import logging

# Configure security logger
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('security.log')
security_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

# Log security events
async def secure_command_handler(context: Context):
    user = context.message.source
    command = context.message.message
    
    # Log command execution
    security_logger.info(f"Command executed: user={user}, command={command}")
    
    try:
        # Command logic
        await context.reply("Command executed")
        security_logger.info(f"Command successful: user={user}")
    except Exception as e:
        security_logger.error(f"Command failed: user={user}, error={e}")
        raise
```

### Simple Intrusion Detection

Monitor for suspicious activity:

```python
import time
from collections import defaultdict

class SecurityMonitor:
    def __init__(self):
        self.failed_attempts = defaultdict(int)
        self.last_attempt = defaultdict(float)
    
    def record_failed_attempt(self, user: str):
        self.failed_attempts[user] += 1
        self.last_attempt[user] = time.time()
        
        # Alert on multiple failures
        if self.failed_attempts[user] >= 5:
            security_logger.warning(f"Multiple failed attempts from {user}")
            # Could send alert message to admin
    
    def is_suspicious(self, user: str) -> bool:
        return self.failed_attempts[user] >= 3

# Usage
security_monitor = SecurityMonitor()

async def protected_command(context: Context):
    user = context.message.source
    
    if security_monitor.is_suspicious(user):
        await context.reply("🚨 Account temporarily restricted")
        return
    
    if not await check_access(context):
        security_monitor.record_failed_attempt(user)
        return
    
    # Command logic here
```

## Security Checklist

### Before Deployment

- [ ] Credentials stored securely (not in code)
- [ ] File permissions set correctly (600/700)
- [ ] `.env` file in `.gitignore`
- [ ] Bot runs as non-root user
- [ ] Firewall configured properly
- [ ] Credentials backed up securely

### Regular Maintenance

- [ ] Update dependencies monthly
- [ ] Review access logs weekly
- [ ] Test backup/restore process quarterly
- [ ] Rotate credentials annually
- [ ] Monitor for security updates

### If Compromised

1. **Immediately stop the bot**
2. **Unlink the Signal device** (Signal app → Settings → Linked devices)
3. **Change all related passwords**
4. **Review logs for unauthorized activity**
5. **Re-link with new credentials**
6. **Update security measures**

!!! tip "Security is a Process"
    Security isn't a one-time setup. Regularly review and update your security practices as your bot grows in importance and usage.

For more operational guidance, see [Running Your Bot](operations.md).