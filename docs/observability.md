---
title: Monitoring & Logging
summary: Monitor your Signal bot's health and debug issues with built-in logging and metrics.
order: 13
---

# Monitoring & Logging

Keep track of your Signal bot's performance and troubleshoot issues with built-in monitoring tools.

## Basic Logging

Signal Client provides structured logging out of the box:

```python
import logging
from signal_client.bot import SignalClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()  # Also log to console
    ]
)

client = SignalClient()
# Your bot will now log important events
```

### Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Development and troubleshooting | Message content, API calls |
| `INFO` | Normal operation | Bot started, commands processed |
| `WARNING` | Recoverable issues | Rate limits, temporary failures |
| `ERROR` | Serious problems | Configuration errors, API failures |

### Environment Variable Control

```bash
# Set log level via environment
export SIGNAL_CLIENT_LOG_LEVEL=DEBUG

# Enable JSON logging for structured logs
export SIGNAL_CLIENT_LOG_FORMAT=json
```

## Performance Metrics

Track your bot's performance with built-in metrics:

```python
import time
from signal_client.bot import SignalClient
from signal_client.context import Context

class MetricsBot(SignalClient):
    def __init__(self):
        super().__init__()
        self.stats = {
            'messages_processed': 0,
            'commands_executed': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    async def handle_message(self, context: Context):
        self.stats['messages_processed'] += 1
        
        try:
            await super().handle_message(context)
            self.stats['commands_executed'] += 1
        except Exception as e:
            self.stats['errors'] += 1
            logging.error(f"Command failed: {e}")
            raise
    
    def get_stats(self):
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'messages_per_minute': self.stats['messages_processed'] / (uptime / 60)
        }

# Usage
bot = MetricsBot()
# Later, check stats
print(bot.get_stats())
```

## Health Checks

Implement health checks for monitoring:

```python
from fastapi import FastAPI
from signal_client.bot import SignalClient
import asyncio

app = FastAPI()
bot = SignalClient()

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring systems."""
    try:
        # Test signal-cli connectivity
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/v1/about", timeout=5)
            response.raise_for_status()
        
        return {
            "status": "healthy",
            "signal_api": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": time.time()
        }, 503

@app.get("/stats")
async def get_stats():
    """Get bot statistics."""
    if hasattr(bot, 'get_stats'):
        return bot.get_stats()
    return {"error": "Stats not available"}

# Run both bot and health check server
async def main():
    # Start health check server in background
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    # Run both concurrently
    await asyncio.gather(
        server.serve(),
        bot.start()
    )
```

## Error Tracking

Track and handle errors systematically:

```python
import traceback
from datetime import datetime
from signal_client.context import Context

class ErrorTracker:
    def __init__(self):
        self.errors = []
        self.max_errors = 100  # Keep last 100 errors
    
    def log_error(self, error: Exception, context: Context = None):
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'user': context.message.source if context else None,
            'message': context.message.message if context else None
        }
        
        self.errors.append(error_info)
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Log to file
        logging.error(f"Bot error: {error_info}")
    
    def get_recent_errors(self, count: int = 10):
        return self.errors[-count:]

# Usage in command handlers
error_tracker = ErrorTracker()

async def safe_command_handler(context: Context):
    try:
        # Your command logic here
        await context.reply("Command executed successfully")
    except Exception as e:
        error_tracker.log_error(e, context)
        await context.reply("Sorry, something went wrong. The error has been logged.")
```

## Simple Monitoring Dashboard

Create a basic web dashboard to monitor your bot:

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Simple monitoring dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Signal Bot Dashboard</title>
        <meta http-equiv="refresh" content="30">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .metric { background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 5px; }
            .healthy { border-left: 5px solid #4CAF50; }
            .unhealthy { border-left: 5px solid #f44336; }
        </style>
    </head>
    <body>
        <h1>🤖 Signal Bot Dashboard</h1>
        
        <div class="metric healthy">
            <h3>Bot Status</h3>
            <p>✅ Running</p>
            <p>Uptime: <span id="uptime">Loading...</span></p>
        </div>
        
        <div class="metric">
            <h3>📊 Statistics</h3>
            <p>Messages processed: <span id="messages">Loading...</span></p>
            <p>Commands executed: <span id="commands">Loading...</span></p>
            <p>Errors: <span id="errors">Loading...</span></p>
        </div>
        
        <script>
            async function updateStats() {
                try {
                    const response = await fetch('/stats');
                    const stats = await response.json();
                    
                    document.getElementById('uptime').textContent = 
                        Math.floor(stats.uptime_seconds / 60) + ' minutes';
                    document.getElementById('messages').textContent = stats.messages_processed;
                    document.getElementById('commands').textContent = stats.commands_executed;
                    document.getElementById('errors').textContent = stats.errors;
                } catch (e) {
                    console.error('Failed to update stats:', e);
                }
            }
            
            // Update stats every 10 seconds
            setInterval(updateStats, 10000);
            updateStats(); // Initial load
        </script>
    </body>
    </html>
    """
```

## Log Analysis

Analyze your bot's logs for insights:

```bash
# Count messages by hour
grep "Message received" bot.log | cut -d' ' -f1-2 | sort | uniq -c

# Find most common errors
grep "ERROR" bot.log | cut -d':' -f4- | sort | uniq -c | sort -nr

# Check response times
grep "Command completed" bot.log | grep -o "took [0-9.]*s" | sort -n

# Monitor specific user activity
grep "+1234567890" bot.log | tail -20
```

## Production Monitoring

For production deployments, consider:

### External Monitoring Services

- **Uptime monitoring** — Use services like UptimeRobot or Pingdom to monitor your health endpoint
- **Log aggregation** — Send logs to services like Papertrail, Loggly, or ELK stack
- **Error tracking** — Use Sentry or Rollbar for detailed error reporting

### System Monitoring

```bash
# Monitor system resources
htop  # CPU and memory usage
df -h  # Disk space
netstat -tlnp | grep 8080  # Network connections

# Monitor Docker containers
docker stats signal-api  # Container resource usage
docker logs -f signal-api  # Container logs
```

### Alerting

Set up basic alerting with cron jobs:

```bash
# Check if bot is running (add to crontab)
*/5 * * * * curl -f http://localhost:8000/health || echo "Bot health check failed" | mail -s "Signal Bot Alert" admin@example.com
```

!!! tip "Start Simple"
    Begin with basic logging and gradually add more sophisticated monitoring as your bot grows in complexity and importance.

For detailed troubleshooting when issues occur, see the [Diagnostics Guide](diagnostics.md).