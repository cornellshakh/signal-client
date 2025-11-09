---
title: Privacy & Trust
summary: Understanding privacy implications and building trustworthy Signal bots.
order: 900
---

# Privacy & Trust

Understanding the privacy implications of Signal bots and how to build trustworthy automation.

## Signal's Privacy Model

Signal provides end-to-end encryption, meaning:

- **Messages are encrypted** between sender and recipient
- **Signal servers can't read** your message content
- **Only linked devices** can decrypt messages

When you create a Signal bot, you're creating a **linked device** that can:
- Read messages sent to your phone number
- Send messages on your behalf
- Access your Signal contacts and groups

## Bot Privacy Considerations

### What Your Bot Can Access

Your Signal bot has access to:

```python
# Message content and metadata
message.message        # "Hello bot!"
message.source         # "+1234567890" 
message.timestamp      # When sent
message.group_id       # Group identifier (if in group)
message.attachments    # Files, images, etc.

# Contact information
# Your bot can see who messages it and group membership
```

### What Your Bot Cannot Access

Your bot **cannot** access:
- Messages sent to other people (unless in shared groups)
- Messages sent before the bot was linked
- Other people's contact lists
- Messages in groups the bot isn't in

### Data Handling Best Practices

#### Minimize Data Collection

Only collect data you actually need:

```python
# ❌ Don't store everything
def store_message(message):
    database.save({
        'content': message.message,
        'sender': message.source,
        'timestamp': message.timestamp,
        'attachments': message.attachments,
        # ... storing everything
    })

# ✅ Store only what's needed
def store_command_usage(command_name, user):
    database.save({
        'command': command_name,
        'user_hash': hash(user),  # Don't store actual phone number
        'timestamp': datetime.now(),
    })
```

#### Secure Data Storage

Protect any data you do store:

```python
import hashlib
import os

def hash_user_id(phone_number: str) -> str:
    """Create anonymous user identifier."""
    salt = os.getenv('USER_HASH_SALT', 'default-salt')
    return hashlib.sha256(f"{phone_number}{salt}".encode()).hexdigest()[:16]

# Use hashed IDs instead of phone numbers
user_id = hash_user_id(context.message.source)
```

#### Data Retention

Don't keep data forever:

```python
import time
from datetime import datetime, timedelta

class DataRetention:
    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
    
    def cleanup_old_data(self):
        """Remove data older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        # Remove old logs, cached data, etc.
        database.delete_where('timestamp < ?', cutoff)
        
        print(f"Cleaned up data older than {self.retention_days} days")

# Run cleanup periodically
retention = DataRetention(retention_days=7)  # Keep only 1 week
```

## Building Trust

### Be Transparent

Tell users what your bot does:

```python
async def privacy_command(context: Context):
    """Explain bot's privacy practices."""
    privacy_info = """
🔒 **Privacy Information**

This bot:
✅ Only reads messages sent directly to it
✅ Stores minimal data (command usage only)
✅ Deletes data after 7 days
✅ Runs on your own server

This bot does NOT:
❌ Store message content
❌ Share data with third parties
❌ Access your other conversations
❌ Send data outside Signal

Source code: https://github.com/yourname/your-bot
    """
    await context.reply(privacy_info)
```

### Provide User Control

Let users control their data:

```python
async def delete_my_data_command(context: Context):
    """Allow users to delete their data."""
    user = context.message.source
    user_hash = hash_user_id(user)
    
    # Delete all data for this user
    deleted_count = database.delete_user_data(user_hash)
    
    await context.reply(f"✅ Deleted {deleted_count} records of your data.")

async def what_data_command(context: Context):
    """Show user what data is stored about them."""
    user = context.message.source
    user_hash = hash_user_id(user)
    
    data = database.get_user_data(user_hash)
    
    if not data:
        await context.reply("No data stored about you.")
        return
    
    summary = f"""
📊 **Your Data**

Commands used: {len(data['commands'])}
Last activity: {data['last_seen']}
Data retention: 7 days

Use `/delete_my_data` to remove all data.
    """
    await context.reply(summary)
```

## Open Source Benefits

Consider making your bot open source:

### Benefits of Open Source Bots

- **Transparency** — Users can see exactly what your bot does
- **Trust** — No hidden functionality or data collection
- **Community** — Others can contribute improvements
- **Security** — More eyes on the code means better security

### Simple Open Source Setup

```bash
# Create public repository
git init
git add .
git commit -m "Initial bot release"

# Add clear README
echo "# My Signal Bot

A simple Signal bot that does X, Y, and Z.

## Privacy
- Only stores command usage statistics
- Deletes data after 7 days
- No message content stored
- Runs on your own server

## Setup
1. Clone this repository
2. Follow setup instructions in docs/
3. Deploy to your own server
" > README.md

# Push to GitHub
git remote add origin https://github.com/yourname/your-bot
git push -u origin main
```

## Privacy-First Bot Examples

### Minimal Data Bot

```python
# A bot that stores no persistent data
from signal_client.bot import SignalClient
from signal_client.context import Context

client = SignalClient()

@client.command("!weather")
async def weather_command(context: Context):
    # Get weather without storing user data
    location = context.message.message.replace("!weather", "").strip()
    weather = await get_weather(location)  # External API call
    
    await context.reply(f"Weather: {weather}")
    # No data stored - completely stateless

@client.command("!time")
async def time_command(context: Context):
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await context.reply(f"Current time: {current_time}")
    # No data stored
```

### Anonymous Analytics Bot

```python
# A bot that collects anonymous usage statistics
import hashlib
from collections import defaultdict

# Anonymous usage tracking
usage_stats = defaultdict(int)

@client.command("!help")
async def help_command(context: Context):
    # Track usage anonymously
    day = datetime.now().strftime("%Y-%m-%d")
    usage_stats[f"help_{day}"] += 1
    
    await context.reply("Available commands: !help, !weather, !time")

# Periodic stats (no user identification)
def print_anonymous_stats():
    print("Anonymous usage statistics:")
    for command, count in usage_stats.items():
        print(f"  {command}: {count} uses")
```

## Legal Considerations

### Terms of Service

Consider adding simple terms:

```python
async def terms_command(context: Context):
    """Display bot terms of service."""
    terms = """
📋 **Terms of Service**

By using this bot, you agree that:
- This is a personal project, not a commercial service
- No warranty or guarantee of uptime
- Your data is handled according to our privacy policy
- You can request data deletion at any time

Questions? Contact: your-email@example.com
    """
    await context.reply(terms)
```

### GDPR Compliance (EU Users)

If you have EU users, consider basic GDPR compliance:

```python
# Implement data subject rights
@client.command("!gdpr")
async def gdpr_command(context: Context):
    """GDPR information and rights."""
    gdpr_info = """
🇪🇺 **GDPR Rights**

You have the right to:
- Know what data we store (/what_data)
- Delete your data (/delete_my_data)
- Data portability (contact admin)
- Object to processing (stop using bot)

Data controller: [Your name/organization]
Contact: [Your email]
    """
    await context.reply(gdpr_info)
```

!!! tip "Privacy by Design"
    The best privacy practice is to not collect data you don't need. Design your bot to be as stateless as possible.

For technical security practices, see [Security & Secrets](production_secrets.md).