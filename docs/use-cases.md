---
title: Use Cases & Examples
summary: Real-world Signal bot examples that developers actually build and deploy.
order: 2
---

# Use Cases & Examples

Signal bots excel at solving specific problems for groups, families, and personal automation. Here are proven patterns that developers use in production.

## Popular Bot Categories

| Bot Type | Use Case | Technical Implementation |
| --- | --- | --- |
| **Group Moderation** | Auto-moderate group chats, welcome members | Message filtering, user management, automated responses |
| **Infrastructure Monitoring** | Server alerts, deployment notifications | Webhook integrations, scheduled health checks, alert routing |
| **Household Automation** | Shared utilities for family/friend groups | Persistent storage, polling mechanisms, simple UIs |
| **Information Services** | Weather, calculations, API lookups | External API integration, data formatting, caching |

## Production Examples

### Group Moderation Bot

A practical group moderator that handles common administrative tasks:

```python
import asyncio
from datetime import datetime
from signal_client.bot import SignalClient
from signal_client.context import Context
from signal_client.command import Command
from signal_client.infrastructure.schemas.requests import SendMessageRequest

class GroupModeratorBot:
    def __init__(self):
        self.client = SignalClient()
        self.setup_commands()
    
    def setup_commands(self):
        # Welcome command for new members
        welcome_cmd = Command(triggers=["!welcome", "!hello"])
        welcome_cmd.with_handler(self.welcome_handler)
        self.client.register(welcome_cmd)
        
        # Rules command
        rules_cmd = Command(triggers=["!rules", "!guidelines"])
        rules_cmd.with_handler(self.rules_handler)
        self.client.register(rules_cmd)
        
        # Member count command
        count_cmd = Command(triggers=["!count", "!members"])
        count_cmd.with_handler(self.member_count_handler)
        self.client.register(count_cmd)
    
    async def welcome_handler(self, context: Context) -> None:
        """Welcome new group members with group info"""
        welcome_msg = SendMessageRequest(
            message="""👋 Welcome to our Signal group!

📋 Quick start:
• Type !rules to see our guidelines
• Type !count to see member count
• Questions? Just ask!

Glad to have you here! 🎉""",
            recipients=[]
        )
        await context.reply(welcome_msg)
    
    async def rules_handler(self, context: Context) -> None:
        """Display group rules and guidelines"""
        rules = SendMessageRequest(
            message="""📋 Group Guidelines:

1. 🤝 Be respectful and constructive
2. 🎯 Keep discussions on-topic
3. 🚫 No spam, excessive self-promotion, or off-topic links
4. 💬 Use replies for long conversations
5. 🔇 Respect others' time zones

Questions about these guidelines? Ask an admin!""",
            recipients=[]
        )
        await context.reply(rules)
    
    async def member_count_handler(self, context: Context) -> None:
        """Show current member count (requires group context)"""
        # Note: This would require group member enumeration via REST API
        response = SendMessageRequest(
            message="👥 Member count feature requires group admin permissions.\nContact an admin for current member statistics.",
            recipients=[]
        )
        await context.reply(response)
    
    async def start(self):
        """Start the moderation bot"""
        print("🛡️ Group Moderator Bot starting...")
        await self.client.start()

# Usage
if __name__ == "__main__":
    bot = GroupModeratorBot()
    asyncio.run(bot.start())
```

### Infrastructure Monitoring Bot

A practical server monitoring bot with webhook integration and scheduled checks:

```python
import asyncio
import aiohttp
import psutil
from datetime import datetime
from signal_client.bot import SignalClient
from signal_client.context import Context
from signal_client.command import Command
from signal_client.infrastructure.schemas.requests import SendMessageRequest

class ServerMonitorBot:
    def __init__(self, alert_recipients: list[str]):
        self.client = SignalClient()
        self.alert_recipients = alert_recipients  # Phone numbers to alert
        self.setup_commands()
    
    def setup_commands(self):
        # Manual status check command
        status_cmd = Command(triggers=["!status", "!health"])
        status_cmd.with_handler(self.status_handler)
        self.client.register(status_cmd)
        
        # Uptime command
        uptime_cmd = Command(triggers=["!uptime"])
        uptime_cmd.with_handler(self.uptime_handler)
        self.client.register(uptime_cmd)
    
    async def status_handler(self, context: Context) -> None:
        """Get current server status"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status_msg = SendMessageRequest(
                message=f"""🖥️ Server Status Report
                
📊 **System Metrics:**
• CPU Usage: {cpu_percent:.1f}%
• Memory: {memory.percent:.1f}% ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)
• Disk: {disk.percent:.1f}% ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)

⏰ **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'✅ All systems normal' if cpu_percent < 80 and memory.percent < 80 else '⚠️ High resource usage detected'}""",
                recipients=[]
            )
            await context.reply(status_msg)
            
        except Exception as e:
            error_msg = SendMessageRequest(
                message=f"❌ Error getting server status: {str(e)}",
                recipients=[]
            )
            await context.reply(error_msg)
    
    async def uptime_handler(self, context: Context) -> None:
        """Get system uptime"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            uptime_msg = SendMessageRequest(
                message=f"""⏱️ System Uptime
                
🚀 **Boot Time:** {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
⏰ **Uptime:** {uptime.days} days, {uptime.seconds // 3600} hours, {(uptime.seconds % 3600) // 60} minutes""",
                recipients=[]
            )
            await context.reply(uptime_msg)
            
        except Exception as e:
            error_msg = SendMessageRequest(
                message=f"❌ Error getting uptime: {str(e)}",
                recipients=[]
            )
            await context.reply(error_msg)
    
    async def send_alert(self, message: str):
        """Send alert to configured recipients"""
        alert_msg = SendMessageRequest(
            message=f"🚨 **ALERT** 🚨\n\n{message}\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            recipients=self.alert_recipients
        )
        # Send via REST API directly (not through command context)
        # Implementation would depend on your specific setup
    
    async def start(self):
        """Start the monitoring bot"""
        print("📊 Server Monitor Bot starting...")
        await self.client.start()

# Usage
if __name__ == "__main__":
    # Configure alert recipients (your phone numbers)
    alert_numbers = ["+1234567890", "+0987654321"]
    bot = ServerMonitorBot(alert_numbers)
    asyncio.run(bot.start())
```

!!! tip "Production deployment"
    For production monitoring, consider:
    
    - **Scheduled checks**: Use `asyncio` tasks or external cron jobs for periodic health checks
    - **Webhook integration**: Accept alerts from monitoring tools like Prometheus, Grafana, or Uptime Robot
    - **Alert throttling**: Prevent spam by limiting alert frequency
    - **Multiple recipients**: Configure different alert levels for different team members

### Household Assistant Bot

A family/household utility bot with persistent storage and practical features:

```python
import asyncio
import json
import os
from datetime import datetime, timedelta
from signal_client.bot import SignalClient
from signal_client.context import Context
from signal_client.command import Command
from signal_client.infrastructure.schemas.requests import SendMessageRequest

class HouseholdBot:
    def __init__(self, data_file: str = "household_data.json"):
        self.client = SignalClient()
        self.data_file = data_file
        self.data = self.load_data()
        self.setup_commands()
    
    def load_data(self) -> dict:
        """Load persistent data from JSON file"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return {"shopping_list": [], "chores": {}, "events": []}
    
    def save_data(self):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def setup_commands(self):
        # Shopping list commands
        shopping_cmd = Command(triggers=["!shopping", "!shop"])
        shopping_cmd.with_handler(self.shopping_handler)
        self.client.register(shopping_cmd)
        
        # Chore tracking
        chores_cmd = Command(triggers=["!chores", "!chore"])
        chores_cmd.with_handler(self.chores_handler)
        self.client.register(chores_cmd)
        
        # Event planning
        events_cmd = Command(triggers=["!events", "!event"])
        events_cmd.with_handler(self.events_handler)
        self.client.register(events_cmd)
        
        # Quick polls
        poll_cmd = Command(triggers=["!poll", "!vote"])
        poll_cmd.with_handler(self.poll_handler)
        self.client.register(poll_cmd)
    
    async def shopping_handler(self, context: Context) -> None:
        """Manage shared shopping list"""
        message_text = context.message.message or ""
        args = message_text.split()[1:]  # Remove command trigger
        
        if not args:
            response = """🛒 **Shopping List Commands:**
• `!shopping list` - Show current list
• `!shopping add <item>` - Add item to list
• `!shopping remove <item>` - Remove item from list
• `!shopping clear` - Clear entire list"""
        
        elif args[0] == "list":
            if self.data["shopping_list"]:
                items = "\n".join(f"• {item}" for item in self.data["shopping_list"])
                response = f"🛒 **Shopping List:**\n{items}"
            else:
                response = "🛒 Shopping list is empty! Add items with `!shopping add <item>`"
        
        elif args[0] == "add" and len(args) > 1:
            item = " ".join(args[1:])
            if item not in self.data["shopping_list"]:
                self.data["shopping_list"].append(item)
                self.save_data()
                response = f"✅ Added '{item}' to shopping list"
            else:
                response = f"ℹ️ '{item}' is already on the list"
        
        elif args[0] == "remove" and len(args) > 1:
            item = " ".join(args[1:])
            if item in self.data["shopping_list"]:
                self.data["shopping_list"].remove(item)
                self.save_data()
                response = f"✅ Removed '{item}' from shopping list"
            else:
                response = f"❌ '{item}' not found on the list"
        
        elif args[0] == "clear":
            self.data["shopping_list"] = []
            self.save_data()
            response = "✅ Shopping list cleared!"
        
        else:
            response = "❌ Invalid command. Use `!shopping` for help."
        
        reply = SendMessageRequest(message=response, recipients=[])
        await context.reply(reply)
    
    async def chores_handler(self, context: Context) -> None:
        """Track household chores and assignments"""
        message_text = context.message.message or ""
        args = message_text.split()[1:]
        
        if not args:
            response = """🧹 **Chore Commands:**
• `!chores list` - Show current chores
• `!chores assign <person> <chore>` - Assign chore
• `!chores done <chore>` - Mark chore as complete
• `!chores reset` - Reset all chores"""
        
        elif args[0] == "list":
            if self.data["chores"]:
                chore_list = []
                for chore, person in self.data["chores"].items():
                    chore_list.append(f"• {chore} → {person}")
                response = f"🧹 **Current Chores:**\n" + "\n".join(chore_list)
            else:
                response = "🧹 No chores assigned!"
        
        elif args[0] == "assign" and len(args) >= 3:
            person = args[1]
            chore = " ".join(args[2:])
            self.data["chores"][chore] = person
            self.save_data()
            response = f"✅ Assigned '{chore}' to {person}"
        
        elif args[0] == "done" and len(args) > 1:
            chore = " ".join(args[1:])
            if chore in self.data["chores"]:
                person = self.data["chores"].pop(chore)
                self.save_data()
                response = f"🎉 {person} completed: {chore}"
            else:
                response = f"❌ Chore '{chore}' not found"
        
        else:
            response = "❌ Invalid command. Use `!chores` for help."
        
        reply = SendMessageRequest(message=response, recipients=[])
        await context.reply(reply)
    
    async def events_handler(self, context: Context) -> None:
        """Simple event planning and reminders"""
        message_text = context.message.message or ""
        args = message_text.split()[1:]
        
        if not args:
            response = """📅 **Event Commands:**
• `!events list` - Show upcoming events
• `!events add <date> <event>` - Add event (YYYY-MM-DD format)
• `!events remove <event>` - Remove event"""
        
        elif args[0] == "list":
            if self.data["events"]:
                event_list = []
                for event in sorted(self.data["events"], key=lambda x: x["date"]):
                    event_list.append(f"• {event['date']}: {event['name']}")
                response = f"📅 **Upcoming Events:**\n" + "\n".join(event_list)
            else:
                response = "📅 No events scheduled!"
        
        elif args[0] == "add" and len(args) >= 3:
            date = args[1]
            event_name = " ".join(args[2:])
            try:
                # Validate date format
                datetime.strptime(date, "%Y-%m-%d")
                self.data["events"].append({"date": date, "name": event_name})
                self.save_data()
                response = f"✅ Added event: {event_name} on {date}"
            except ValueError:
                response = "❌ Invalid date format. Use YYYY-MM-DD (e.g., 2024-12-25)"
        
        else:
            response = "❌ Invalid command. Use `!events` for help."
        
        reply = SendMessageRequest(message=response, recipients=[])
        await context.reply(reply)
    
    async def poll_handler(self, context: Context) -> None:
        """Quick decision polls"""
        message_text = context.message.message or ""
        
        if "dinner" in message_text.lower():
            options = ["Pizza 🍕", "Chinese 🥡", "Cook at home 👨‍🍳", "Order something new 🎲"]
            poll_msg = "🍽️ **What's for dinner tonight?**\n" + "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
        elif "movie" in message_text.lower():
            options = ["Action 🎬", "Comedy 😂", "Drama 🎭", "Documentary 📚"]
            poll_msg = "🎬 **Movie night - what genre?**\n" + "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options))
        else:
            poll_msg = """📊 **Quick Polls Available:**
• `!poll dinner` - Dinner decision
• `!poll movie` - Movie genre choice

Or create custom polls with specific options!"""
        
        reply = SendMessageRequest(message=poll_msg, recipients=[])
        await context.reply(reply)
    
    async def start(self):
        """Start the household bot"""
        print("🏠 Household Assistant Bot starting...")
        await self.client.start()

# Usage
if __name__ == "__main__":
    bot = HouseholdBot()
    asyncio.run(bot.start())
```

!!! note "Data persistence"
    This bot uses JSON file storage for simplicity. For production use, consider:
    
    - **SQLite database**: Better for complex queries and concurrent access
    - **Redis**: For high-performance caching and pub/sub features
    - **Cloud storage**: For multi-device synchronization

## API Integration Example

Here's a practical bot that integrates with external APIs for weather and other services:

```python
import asyncio
import aiohttp
from signal_client.bot import SignalClient
from signal_client.context import Context
from signal_client.command import Command
from signal_client.infrastructure.schemas.requests import SendMessageRequest

class APIBot:
    def __init__(self, weather_api_key: str):
        self.client = SignalClient()
        self.weather_api_key = weather_api_key
        self.setup_commands()
    
    def setup_commands(self):
        # Weather command
        weather_cmd = Command(triggers=["!weather", "!w"])
        weather_cmd.with_handler(self.weather_handler)
        self.client.register(weather_cmd)
        
        # Random fact command
        fact_cmd = Command(triggers=["!fact", "!random"])
        fact_cmd.with_handler(self.fact_handler)
        self.client.register(fact_cmd)
    
    async def weather_handler(self, context: Context) -> None:
        """Get weather information for a city"""
        message_text = context.message.message or ""
        args = message_text.split()[1:]  # Remove command trigger
        
        if not args:
            response = "❌ Please specify a city: `!weather New York`"
        else:
            city = " ".join(args)
            weather_data = await self.get_weather(city)
            response = weather_data
        
        reply = SendMessageRequest(message=response, recipients=[])
        await context.reply(reply)
    
    async def get_weather(self, city: str) -> str:
        """Fetch weather data from OpenWeatherMap API"""
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": self.weather_api_key,
                "units": "metric"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        temp = data["main"]["temp"]
                        description = data["weather"][0]["description"]
                        humidity = data["main"]["humidity"]
                        
                        return f"""🌤️ **Weather in {city}:**
• Temperature: {temp}°C
• Conditions: {description.title()}
• Humidity: {humidity}%"""
                    else:
                        return f"❌ Could not find weather data for '{city}'"
        
        except Exception as e:
            return f"❌ Error fetching weather: {str(e)}"
    
    async def fact_handler(self, context: Context) -> None:
        """Get a random interesting fact"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://uselessfacts.jsph.pl/random.json?language=en") as response:
                    if response.status == 200:
                        data = await response.json()
                        fact = data["text"]
                        response_text = f"🧠 **Random Fact:**\n{fact}"
                    else:
                        response_text = "❌ Could not fetch a random fact right now"
        
        except Exception as e:
            response_text = f"❌ Error fetching fact: {str(e)}"
        
        reply = SendMessageRequest(message=response_text, recipients=[])
        await context.reply(reply)
    
    async def start(self):
        """Start the API bot"""
        print("🌐 API Integration Bot starting...")
        await self.client.start()

# Usage
if __name__ == "__main__":
    # Get your free API key from https://openweathermap.org/api
    WEATHER_API_KEY = "your_openweathermap_api_key_here"
    
    bot = APIBot(WEATHER_API_KEY)
    asyncio.run(bot.start())
```

!!! tip "API best practices"
    - **Rate limiting**: Implement request throttling for external APIs
    - **Error handling**: Always handle API failures gracefully
    - **Caching**: Cache responses to reduce API calls and improve performance
    - **API keys**: Store sensitive keys in environment variables, not code

## Development Workflow

### 1. Start Simple
Pick one specific problem your bot will solve. Examples:
- Group welcome messages
- Server status checks
- Shared shopping lists
- Weather lookups

### 2. Set Up Development Environment
```bash
# Follow the quickstart guide first
# Then create a development structure:
mkdir my-signal-bot
cd my-signal-bot
python -m venv venv
source venv/bin/activate
pip install signal-client
```

### 3. Test in Isolation
Create a private Signal group for testing:
- Add only your bot and test accounts
- Test all commands thoroughly
- Handle edge cases and errors

### 4. Deploy and Monitor
- Use environment variables for configuration
- Implement logging for debugging
- Set up health checks and monitoring
- Plan for graceful shutdowns and restarts

!!! warning "Production considerations"
    - **Security**: Never commit API keys or phone numbers to version control
    - **Reliability**: Implement proper error handling and recovery mechanisms
    - **Scalability**: Consider message rate limits and concurrent user handling
    - **Monitoring**: Log important events and set up alerting for failures

## Next Steps

Ready to build your own Signal bot? Here's your path forward:

1. **[Quickstart Guide](quickstart.md)** — Set up your development environment
2. **[API Reference](api-reference.md)** — Explore all available methods and classes
3. **[Configuration Guide](configuration.md)** — Learn about production configuration options
4. **[Writing Commands](guides/writing-async-commands.md)** — Master advanced command patterns

!!! example "Community examples"
    Looking for more inspiration? Check out these community-built bots:
    
    - **Home automation**: Control smart devices via Signal commands
    - **CI/CD notifications**: Get build and deployment alerts
    - **Expense tracking**: Log and categorize shared expenses
    - **Meeting scheduler**: Coordinate group meetings and events
