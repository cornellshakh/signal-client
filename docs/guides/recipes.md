---
title: Bot Recipes
summary: Practical code examples and patterns for building useful Signal bots.
order: 210
---

# Bot Recipes

Ready-to-use code patterns for common Signal bot functionality. Copy, modify, and adapt these examples for your own projects.

## File Sharing Bot

Share files securely through Signal with automatic cleanup and access control.

```python
import os
import base64
from signal_client.bot import SignalClient
from signal_client.command import Command
from signal_client.infrastructure.schemas.requests import SendMessageRequest

# Authorized users who can request files
AUTHORIZED_USERS = ["+1234567890", "+0987654321"]

async def share_file_handler(context: Context) -> None:
    """Handle file sharing requests: 'share filename.pdf'"""
    if context.message.source not in AUTHORIZED_USERS:
        await context.reply(SendMessageRequest(
            message="❌ Unauthorized access",
            recipients=[]
        ))
        return
    
    # Extract filename from message
    message_text = context.message.message or ""
    parts = message_text.split()
    
    if len(parts) < 2:
        await context.reply(SendMessageRequest(
            message="Usage: share <filename>",
            recipients=[]
        ))
        return
    
    filename = parts[1]
    file_path = f"/secure/files/{filename}"
    
    if not os.path.exists(file_path):
        await context.reply(SendMessageRequest(
            message=f"❌ File '{filename}' not found",
            recipients=[]
        ))
        return
    
    try:
        # Read and encode file
        with open(file_path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode()
        
        # Send file as attachment
        response = SendMessageRequest(
            message=f"📎 {filename}",
            recipients=[],
            base64_attachments=[file_data]
        )
        await context.reply(response)
        
        print(f"File {filename} shared with {context.message.source}")
        
    except Exception as e:
        await context.reply(SendMessageRequest(
            message=f"❌ Error sharing file: {str(e)}",
            recipients=[]
        ))

# Register command
client = SignalClient()
share_cmd = Command(triggers=["share"])
share_cmd.with_handler(share_file_handler)
client.register(share_cmd)
```

!!! tip "Security Considerations"
    - Store files outside your bot's code directory
    - Implement file size limits to prevent abuse
    - Log all file access for audit purposes
    - Consider automatic file expiration

## Weather Bot with Caching

Get weather information with smart caching to avoid API rate limits.

```python
import asyncio
import json
import time
from typing import Dict, Optional
import httpx
from signal_client.context import Context
from signal_client.infrastructure.schemas.requests import SendMessageRequest

class WeatherBot:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache: Dict[str, Dict] = {}
        self.cache_duration = 600  # 10 minutes
    
    def get_cached_weather(self, city: str) -> Optional[Dict]:
        """Get weather from cache if still valid."""
        if city in self.cache:
            cached_data = self.cache[city]
            if time.time() - cached_data['timestamp'] < self.cache_duration:
                return cached_data['data']
        return None
    
    def cache_weather(self, city: str, data: Dict) -> None:
        """Cache weather data with timestamp."""
        self.cache[city] = {
            'data': data,
            'timestamp': time.time()
        }
    
    async def get_weather(self, city: str) -> str:
        """Get weather for a city with caching."""
        # Check cache first
        cached = self.get_cached_weather(city)
        if cached:
            return self.format_weather(cached, from_cache=True)
        
        # Fetch from API
        try:
            async with httpx.AsyncClient() as client:
                url = f"http://api.openweathermap.org/data/2.5/weather"
                params = {
                    'q': city,
                    'appid': self.api_key,
                    'units': 'metric'
                }
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                self.cache_weather(city, data)
                return self.format_weather(data, from_cache=False)
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"❌ City '{city}' not found"
            else:
                return f"❌ Weather service error: {e.response.status_code}"
        except Exception as e:
            return f"❌ Error getting weather: {str(e)}"
    
    def format_weather(self, data: Dict, from_cache: bool = False) -> str:
        """Format weather data for display."""
        city = data['name']
        country = data['sys']['country']
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        description = data['weather'][0]['description'].title()
        humidity = data['main']['humidity']
        
        cache_indicator = " 📋" if from_cache else ""
        
        return f"""🌤️ Weather for {city}, {country}{cache_indicator}
        
🌡️ Temperature: {temp}°C (feels like {feels_like}°C)
☁️ Conditions: {description}
💧 Humidity: {humidity}%"""

# Initialize weather bot
weather_bot = WeatherBot(api_key="your_openweather_api_key")

async def weather_handler(context: Context) -> None:
    """Handle weather requests: 'weather London' or 'weather New York'"""
    message_text = context.message.message or ""
    parts = message_text.split(maxsplit=1)
    
    if len(parts) < 2:
        await context.reply(SendMessageRequest(
            message="Usage: weather <city name>\nExample: weather London",
            recipients=[]
        ))
        return
    
    city = parts[1].strip()
    if not city:
        await context.reply(SendMessageRequest(
            message="Please specify a city name",
            recipients=[]
        ))
        return
    
    # Show typing indicator (if supported)
    await context.react("⏳")
    
    # Get weather data
    weather_info = await weather_bot.get_weather(city)
    
    # Remove typing indicator and send response
    await context.remove_reaction()
    await context.reply(SendMessageRequest(
        message=weather_info,
        recipients=[]
    ))

# Register command with regex for flexible matching
import re
weather_cmd = Command(triggers=[
    re.compile(r"weather\s+(.+)", re.IGNORECASE),
    re.compile(r"forecast\s+(.+)", re.IGNORECASE)
])
weather_cmd.with_handler(weather_handler)
```

!!! note "API Setup"
    Get a free API key from [OpenWeatherMap](https://openweathermap.org/api) and replace `"your_openweather_api_key"` with your actual key.

## Reminder Bot with Persistence

Set reminders that persist across bot restarts using SQLite storage.

```python
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import List, Tuple
from signal_client.context import Context
from signal_client.infrastructure.schemas.requests import SendMessageRequest

class ReminderBot:
    def __init__(self, db_path: str = "reminders.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for reminders."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_number TEXT NOT NULL,
                message TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE
            )
        """)
        conn.commit()
        conn.close()
    
    def add_reminder(self, user_number: str, message: str, remind_at: datetime) -> int:
        """Add a new reminder."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "INSERT INTO reminders (user_number, message, remind_at) VALUES (?, ?, ?)",
            (user_number, message, remind_at)
        )
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reminder_id
    
    def get_due_reminders(self) -> List[Tuple]:
        """Get all reminders that are due."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT id, user_number, message FROM reminders 
            WHERE remind_at <= ? AND completed = FALSE
        """, (datetime.now(),))
        reminders = cursor.fetchall()
        conn.close()
        return reminders
    
    def mark_completed(self, reminder_id: int):
        """Mark a reminder as completed."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE reminders SET completed = TRUE WHERE id = ?",
            (reminder_id,)
        )
        conn.commit()
        conn.close()

# Initialize reminder bot
reminder_bot = ReminderBot()

async def remind_handler(context: Context) -> None:
    """Handle reminder creation: 'remind me in 30 minutes to check email'"""
    message_text = context.message.message or ""
    
    # Parse reminder format: "remind me in X minutes/hours to Y"
    import re
    pattern = r"remind me in (\d+) (minutes?|hours?) to (.+)"
    match = re.search(pattern, message_text, re.IGNORECASE)
    
    if not match:
        await context.reply(SendMessageRequest(
            message="""Usage examples:
• remind me in 30 minutes to check email
• remind me in 2 hours to call mom
• remind me in 1 hour to take medication""",
            recipients=[]
        ))
        return
    
    amount = int(match.group(1))
    unit = match.group(2).lower()
    reminder_text = match.group(3)
    
    # Calculate reminder time
    if unit.startswith('minute'):
        remind_at = datetime.now() + timedelta(minutes=amount)
    elif unit.startswith('hour'):
        remind_at = datetime.now() + timedelta(hours=amount)
    else:
        await context.reply(SendMessageRequest(
            message="❌ Invalid time unit. Use 'minutes' or 'hours'",
            recipients=[]
        ))
        return
    
    # Store reminder
    reminder_id = reminder_bot.add_reminder(
        context.message.source,
        reminder_text,
        remind_at
    )
    
    # Confirm creation
    time_str = remind_at.strftime("%I:%M %p on %B %d")
    await context.reply(SendMessageRequest(
        message=f"✅ Reminder set for {time_str}\n📝 {reminder_text}",
        recipients=[]
    ))

async def check_reminders_task(client):
    """Background task to check and send due reminders."""
    while True:
        try:
            due_reminders = reminder_bot.get_due_reminders()
            
            for reminder_id, user_number, message in due_reminders:
                # Send reminder
                reminder_msg = SendMessageRequest(
                    message=f"⏰ Reminder: {message}",
                    recipients=[user_number]
                )
                
                # Send through client (you'll need to implement this)
                # await client.send_message(reminder_msg)
                
                # Mark as completed
                reminder_bot.mark_completed(reminder_id)
                print(f"Sent reminder to {user_number}: {message}")
            
            # Check every minute
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"Error checking reminders: {e}")
            await asyncio.sleep(60)

# Register command
remind_cmd = Command(triggers=[
    re.compile(r"remind me in \d+ (?:minutes?|hours?) to .+", re.IGNORECASE)
])
remind_cmd.with_handler(remind_handler)
```

## Group Chat Moderator

Automatically moderate group chats with configurable rules and actions.

```python
import re
from typing import Set, List
from signal_client.context import Context
from signal_client.infrastructure.schemas.requests import SendMessageRequest

class GroupModerator:
    def __init__(self):
        # Configurable word filters
        self.banned_words: Set[str] = {
            "spam", "advertisement", "promotion"  # Add your words
        }
        
        # Admin users who can manage the bot
        self.admins: Set[str] = {
            "+1234567890"  # Add admin phone numbers
        }
        
        # Warning counts per user
        self.warnings: dict = {}
        self.max_warnings = 3
    
    def is_admin(self, user_number: str) -> bool:
        """Check if user is an admin."""
        return user_number in self.admins
    
    def contains_banned_content(self, message: str) -> List[str]:
        """Check if message contains banned content."""
        message_lower = message.lower()
        found_words = []
        
        for word in self.banned_words:
            if word in message_lower:
                found_words.append(word)
        
        return found_words
    
    def add_warning(self, user_number: str) -> int:
        """Add warning to user and return total warnings."""
        self.warnings[user_number] = self.warnings.get(user_number, 0) + 1
        return self.warnings[user_number]
    
    def should_kick_user(self, user_number: str) -> bool:
        """Check if user should be kicked based on warnings."""
        return self.warnings.get(user_number, 0) >= self.max_warnings

# Initialize moderator
moderator = GroupModerator()

async def moderate_message(context: Context) -> None:
    """Moderate all group messages."""
    # Only moderate group messages
    if not context.message.is_group():
        return
    
    # Don't moderate admin messages
    if moderator.is_admin(context.message.source):
        return
    
    message_text = context.message.message or ""
    banned_words = moderator.contains_banned_content(message_text)
    
    if banned_words:
        # Add warning
        warning_count = moderator.add_warning(context.message.source)
        
        # React to the problematic message
        await context.react("⚠️")
        
        if moderator.should_kick_user(context.message.source):
            # Final warning before kick
            await context.reply(SendMessageRequest(
                message=f"🚫 User has reached maximum warnings ({moderator.max_warnings}). Please remove from group.",
                recipients=[]
            ))
        else:
            # Send warning
            remaining = moderator.max_warnings - warning_count
            await context.reply(SendMessageRequest(
                message=f"⚠️ Warning {warning_count}/{moderator.max_warnings}: Please keep messages appropriate. {remaining} warnings remaining.",
                recipients=[]
            ))

async def admin_commands(context: Context) -> None:
    """Handle admin commands for moderation."""
    if not moderator.is_admin(context.message.source):
        await context.reply(SendMessageRequest(
            message="❌ Admin access required",
            recipients=[]
        ))
        return
    
    message_text = context.message.message or ""
    
    if message_text.startswith("!warnings"):
        # Show warning counts
        if moderator.warnings:
            warning_list = "\n".join([
                f"• {number}: {count} warnings"
                for number, count in moderator.warnings.items()
            ])
            await context.reply(SendMessageRequest(
                message=f"📊 Warning counts:\n{warning_list}",
                recipients=[]
            ))
        else:
            await context.reply(SendMessageRequest(
                message="📊 No warnings issued yet",
                recipients=[]
            ))
    
    elif message_text.startswith("!clear"):
        # Clear warnings for a user
        parts = message_text.split()
        if len(parts) == 2:
            user_number = parts[1]
            if user_number in moderator.warnings:
                del moderator.warnings[user_number]
                await context.reply(SendMessageRequest(
                    message=f"✅ Cleared warnings for {user_number}",
                    recipients=[]
                ))
            else:
                await context.reply(SendMessageRequest(
                    message=f"ℹ️ No warnings found for {user_number}",
                    recipients=[]
                ))

# Register commands
# Moderate all messages (no specific trigger)
moderate_cmd = Command(triggers=[""])  # Empty trigger matches all messages
moderate_cmd.with_handler(moderate_message)

# Admin commands
admin_cmd = Command(triggers=["!warnings", "!clear"])
admin_cmd.with_handler(admin_commands)
```

!!! warning "Group Management"
    Signal bots cannot automatically remove users from groups. The bot can only warn about problematic users - group admins must manually remove them.
