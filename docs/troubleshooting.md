---
title: Troubleshooting & Diagnostics
summary: Complete guide to diagnosing and resolving Signal Client issues, error handling patterns, and debugging techniques.
order: 400
---

# Troubleshooting & Diagnostics

This comprehensive guide covers common Signal Client issues, diagnostic techniques, error handling patterns, and step-by-step resolution procedures.

## Quick Diagnostic Checklist

When your Signal Client bot isn't working, run through this checklist first:

```bash
# 1. Check if signal-cli REST API is running
curl -f http://localhost:8080/v1/about || echo "❌ REST API not responding"

# 2. Verify Signal device is linked
curl -s http://localhost:8080/v1/accounts | jq '.' || echo "❌ No linked accounts"

# 3. Check credential file permissions
ls -la ~/.local/share/signal-api/data/*/
# Should show 600 permissions on files, 700 on directories

# 4. Test basic message sending
curl -X POST http://localhost:8080/v2/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Test", "recipients": ["+1234567890"], "number": "+1234567890"}'

# 5. Check bot logs for errors
tail -f /var/log/signal-client.log
```

## Common Issues & Solutions

### 1. Signal Device Not Linked

#### Symptoms
```
ERROR - AuthenticationError: Signal device is not properly linked
ConnectionError: HTTP 400: Device not registered
```

#### Diagnosis
```bash
# Check if any accounts are registered
curl -s http://localhost:8080/v1/accounts

# Expected: [""+1234567890""] (your phone number)
# If empty: [] - device not linked
```

#### Solution
```bash
# 1. Stop any running signal-cli containers
docker stop signal-api
docker rm signal-api

# 2. Clear old credentials (if corrupted)
rm -rf ~/.local/share/signal-api/data/*

# 3. Start fresh REST API
docker run -d --name signal-api \
  -p 8080:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest

# 4. Wait for startup (10-15 seconds)
sleep 15

# 5. Generate QR code for linking
echo "Open: http://localhost:8080/v1/qrcodelink?device_name=signal-bot"

# 6. Scan QR code with Signal mobile app
# Signal Settings > Linked devices > "+" > Scan QR code

# 7. Verify linking worked
curl -s http://localhost:8080/v1/accounts | jq '.'
```

#### Prevention
- Set up monitoring to check account status regularly
- Implement automatic re-linking procedures
- Use health checks in production deployments

### 2. REST API Connection Issues

#### Symptoms
```
ConnectionError: Cannot connect to signal-cli REST API
requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=8080)
```

#### Diagnosis
```bash
# Check if Docker container is running
docker ps | grep signal-api

# Check container logs
docker logs signal-api

# Test network connectivity
telnet localhost 8080
# or
nc -zv localhost 8080

# Check if port is bound
netstat -tlnp | grep 8080
# or
ss -tlnp | grep 8080
```

#### Solution

**If container is not running:**
```bash
# Start the container
docker run -d --name signal-api \
  -p 8080:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest
```

**If container is running but not responding:**
```bash
# Restart the container
docker restart signal-api

# Wait for startup
sleep 15

# Test connectivity
curl -f http://localhost:8080/v1/about
```

**If port is already in use:**
```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process or use different port
docker run -d --name signal-api \
  -p 8081:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest

# Update your bot configuration
export SIGNAL_CLIENT_REST_URL="http://localhost:8081"
```

### 3. Message Sending Failures

#### Symptoms
```
MessageSendError: Failed to send message
HTTP 400: Invalid recipient
HTTP 500: Internal server error
```

#### Diagnosis
```bash
# Test message sending manually
curl -X POST http://localhost:8080/v2/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test message",
    "recipients": ["+1234567890"],
    "number": "+1234567890"
  }'

# Check signal-cli logs
docker logs signal-api | tail -20

# Verify recipient phone number format
# Must be in international format: +1234567890
```

#### Solution

**Invalid phone number format:**
```python
import re

def validate_phone_number(phone: str) -> str:
    """Validate and format phone number."""
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone)
    
    # Add country code if missing (assuming US)
    if len(digits) == 10:
        digits = '1' + digits
    
    # Format as international
    return '+' + digits

# Usage
recipient = validate_phone_number("(555) 123-4567")  # Returns "+15551234567"
```

**Rate limiting issues:**
```python
import asyncio
from signal_client.exceptions import RateLimitError

async def send_with_retry(context: Context, request: SendMessageRequest, max_retries: int = 3):
    """Send message with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            await context.send(request)
            return
        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                await asyncio.sleep(wait_time)
            else:
                raise
```

**Signal server connectivity:**
```bash
# Test Signal server connectivity
curl -I https://textsecure-service.whispersystems.org/

# Check DNS resolution
nslookup textsecure-service.whispersystems.org

# Test from container
docker exec signal-api curl -I https://textsecure-service.whispersystems.org/
```

### 4. Permission and File Access Issues

#### Symptoms
```
PermissionError: [Errno 13] Permission denied: '/home/.local/share/signal-cli/data'
FileNotFoundError: [Errno 2] No such file or directory: 'account.json'
```

#### Diagnosis
```bash
# Check file permissions
ls -la ~/.local/share/signal-api/
ls -la ~/.local/share/signal-api/data/*/

# Check ownership
stat ~/.local/share/signal-api/

# Check if files exist
find ~/.local/share/signal-api -name "*.json" -ls
```

#### Solution
```bash
# Fix permissions
chmod 700 ~/.local/share/signal-api
find ~/.local/share/signal-api -type d -exec chmod 700 {} \;
find ~/.local/share/signal-api -type f -exec chmod 600 {} \;

# Fix ownership (if needed)
sudo chown -R $USER:$USER ~/.local/share/signal-api

# For Docker containers, ensure volume permissions
docker run -d --name signal-api \
  -p 8080:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  -u $(id -u):$(id -g) \
  bbernhard/signal-cli-rest-api:latest
```

### 5. Configuration Issues

#### Symptoms
```
ConfigurationError: Required configuration missing
KeyError: 'SIGNAL_CLIENT_NUMBER'
ValueError: Invalid configuration format
```

#### Diagnosis
```bash
# Check environment variables
env | grep SIGNAL_CLIENT

# Verify configuration file
cat ~/.config/signal-client/config.toml

# Test configuration loading
python -c "
from signal_client.config import load_config
try:
    config = load_config()
    print('Configuration loaded successfully')
    print(f'Phone number: {config.phone_number}')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

#### Solution

**Missing environment variables:**
```bash
# Set required environment variables
export SIGNAL_CLIENT_NUMBER="+1234567890"
export SIGNAL_CLIENT_REST_URL="http://localhost:8080"
export SIGNAL_CLIENT_SECRETS_DIR="$HOME/.local/share/signal-api"

# Make permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export SIGNAL_CLIENT_NUMBER="+1234567890"' >> ~/.bashrc
```

**Invalid configuration file:**
```toml
# ~/.config/signal-client/config.toml
[signal_client]
phone_number = "+1234567890"
rest_url = "http://localhost:8080"
secrets_dir = "/home/user/.local/share/signal-api"

[logging]
level = "INFO"
format = "json"

[worker]
pool_size = 4
queue_size = 200
```

### 6. Import and Module Issues

#### Symptoms
```
ImportError: No module named 'signal_client'
ModuleNotFoundError: No module named 'signal_client.bot'
AttributeError: module 'signal_client' has no attribute 'SignalClient'
```

#### Diagnosis
```bash
# Check if signal-client is installed
pip list | grep signal-client

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Test import
python -c "
try:
    import signal_client
    print('signal_client imported successfully')
    print(f'Version: {signal_client.__version__}')
except ImportError as e:
    print(f'Import error: {e}')
"
```

#### Solution
```bash
# Install signal-client
pip install signal-client

# Or upgrade if already installed
pip install --upgrade signal-client

# For development installation
pip install -e .

# Check virtual environment
which python
which pip

# Activate correct environment
source venv/bin/activate  # or your environment name
```

### 7. Docker and Container Issues

#### Symptoms
```
docker: Error response from daemon: port is already allocated
docker: Error response from daemon: Conflict. The container name "/signal-api" is already in use
```

#### Diagnosis
```bash
# Check running containers
docker ps -a

# Check port usage
docker port signal-api

# Check container logs
docker logs signal-api

# Check Docker daemon status
systemctl status docker  # Linux
# or
docker version
```

#### Solution

**Port conflicts:**
```bash
# Stop conflicting container
docker stop signal-api
docker rm signal-api

# Use different port
docker run -d --name signal-api \
  -p 8081:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest
```

**Container name conflicts:**
```bash
# Remove existing container
docker rm signal-api

# Or use different name
docker run -d --name signal-api-new \
  -p 8080:8080 \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest
```

**Volume mount issues:**
```bash
# Ensure directory exists
mkdir -p ~/.local/share/signal-api

# Fix permissions
chmod 755 ~/.local/share/signal-api

# Use absolute path
docker run -d --name signal-api \
  -p 8080:8080 \
  -v "$(pwd)/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest
```

## Advanced Debugging Techniques

### Enable Debug Logging

```python
import logging
import os

# Set debug level
os.environ['SIGNAL_CLIENT_LOG_LEVEL'] = 'DEBUG'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/signal-client-debug.log'),
        logging.StreamHandler()
    ]
)

# Your bot code here
```

### Network Traffic Analysis

```bash
# Monitor HTTP traffic to signal-cli REST API
sudo tcpdump -i lo -A -s 0 'port 8080'

# Or use netcat to test API manually
echo '{"message": "test", "recipients": ["+1234567890"], "number": "+1234567890"}' | \
  nc -w 3 localhost 8080
```

### Signal-CLI Direct Debugging

```bash
# Run signal-cli directly (without REST API)
docker run -it --rm \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest \
  signal-cli --config /home/.local/share/signal-cli -u +1234567890 listAccounts

# Send test message directly
docker run -it --rm \
  -v "$HOME/.local/share/signal-api:/home/.local/share/signal-cli" \
  bbernhard/signal-cli-rest-api:latest \
  signal-cli --config /home/.local/share/signal-cli -u +1234567890 send -m "Test" +1234567890
```

### Memory and Performance Issues

```python
import psutil
import asyncio
from signal_client.bot import SignalClient

class MonitoredSignalClient(SignalClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = time.time()
        
    async def start(self):
        """Start with monitoring."""
        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"Starting bot - Initial memory: {initial_memory:.1f} MB")
        
        # Start monitoring task
        asyncio.create_task(self.monitor_resources())
        
        await super().start()
    
    async def monitor_resources(self):
        """Monitor resource usage."""
        while True:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            print(f"Memory: {memory_mb:.1f} MB, CPU: {cpu_percent:.1f}%")
            
            # Alert if memory usage is high
            if memory_mb > 500:  # 500 MB threshold
                print("WARNING: High memory usage detected!")
            
            await asyncio.sleep(60)  # Check every minute
```

## Error Handling Patterns

### Robust Message Handler

```python
import asyncio
import logging
from typing import Optional
from signal_client.context import Context
from signal_client.infrastructure.schemas.requests import SendMessageRequest
from signal_client.exceptions import (
    MessageSendError, 
    RateLimitError, 
    ConnectionError,
    AuthenticationError
)

logger = logging.getLogger(__name__)

async def robust_message_handler(context: Context) -> None:
    """Example of robust error handling in message handlers."""
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            # Your message processing logic
            response_text = await process_message(context.message.message)
            
            response = SendMessageRequest(
                message=response_text,
                recipients=[]
            )
            
            await context.reply(response)
            
            # Success - log and return
            logger.info(f"Message processed successfully for {context.message.source}")
            return
            
        except RateLimitError:
            # Rate limited - wait and retry
            wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
            logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
            await asyncio.sleep(wait_time)
            
        except AuthenticationError:
            # Authentication failed - cannot retry
            logger.error("Authentication failed - device may be unlinked")
            await send_error_notification("Authentication failed - please check device linking")
            break
            
        except ConnectionError:
            # Connection failed - retry with backoff
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"Connection failed, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Connection failed after all retries")
                await send_error_notification("Connection to Signal failed")
                
        except MessageSendError as e:
            # Message send failed - log details and retry
            logger.error(f"Failed to send message: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                await send_error_notification(f"Failed to send message after {max_retries} attempts")
                
        except Exception as e:
            # Unexpected error - log and notify
            logger.exception(f"Unexpected error in message handler: {e}")
            await send_error_notification(f"Unexpected error: {type(e).__name__}")
            break

async def process_message(message: Optional[str]) -> str:
    """Process the incoming message and return response."""
    if not message:
        return "I didn't receive any message content."
    
    # Your processing logic here
    return f"Processed: {message}"

async def send_error_notification(error_msg: str) -> None:
    """Send error notification to administrators."""
    # Implementation depends on your notification system
    logger.error(f"Error notification: {error_msg}")
```

### Circuit Breaker Pattern

```python
import time
from enum import Enum
from typing import Callable, Any

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# Usage
circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)

async def protected_send_message(context: Context, request: SendMessageRequest):
    """Send message with circuit breaker protection."""
    return await circuit_breaker.call(context.send, request)
```

## Production Monitoring & Alerting

### Health Check Endpoint

```python
from fastapi import FastAPI, HTTPException
import asyncio
import aiohttp

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    checks = {
        "signal_api": await check_signal_api(),
        "credentials": check_credentials(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }
    
    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": checks})

async def check_signal_api() -> bool:
    """Check if signal-cli REST API is responding."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/v1/about", timeout=5) as response:
                return response.status == 200
    except:
        return False

def check_credentials() -> bool:
    """Check if Signal credentials exist and are readable."""
    import os
    secrets_dir = os.environ.get('SIGNAL_CLIENT_SECRETS_DIR', '~/.local/share/signal-api')
    secrets_path = os.path.expanduser(secrets_dir)
    
    try:
        # Check if data directory exists and has content
        data_dir = os.path.join(secrets_path, 'data')
        return os.path.exists(data_dir) and len(os.listdir(data_dir)) > 0
    except:
        return False

def check_disk_space() -> bool:
    """Check available disk space."""
    import shutil
    total, used, free = shutil.disk_usage("/")
    free_percent = (free / total) * 100
    return free_percent > 10  # Alert if less than 10% free

def check_memory_usage() -> bool:
    """Check memory usage."""
    import psutil
    memory = psutil.virtual_memory()
    return memory.percent < 90  # Alert if more than 90% used
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Metrics
message_counter = Counter('signal_messages_total', 'Total messages processed', ['command', 'status'])
message_duration = Histogram('signal_message_duration_seconds', 'Message processing duration')
active_connections = Gauge('signal_active_connections', 'Active Signal connections')
error_counter = Counter('signal_errors_total', 'Total errors', ['error_type'])

class MetricsMiddleware:
    async def before_command(self, context: Context) -> bool:
        context._start_time = time.time()
        return True
    
    async def after_command(self, context: Context) -> None:
        duration = time.time() - context._start_time
        message_duration.observe(duration)
        message_counter.labels(command='unknown', status='success').inc()
    
    async def on_error(self, error: Exception, context: Context) -> None:
        error_counter.labels(error_type=type(error).__name__).inc()
        message_counter.labels(command='unknown', status='error').inc()

# Start metrics server
start_http_server(9300)
```

## Debugging Checklist

When troubleshooting Signal Client issues, work through this systematic checklist:

### Environment Check
- [ ] Python version 3.9+ installed
- [ ] signal-client package installed and up-to-date
- [ ] Required environment variables set
- [ ] Configuration file valid (if used)

### Signal Setup Check
- [ ] signal-cli REST API container running
- [ ] REST API responding on correct port
- [ ] Signal device properly linked
- [ ] Credentials directory exists with correct permissions
- [ ] Account shows up in `/v1/accounts` endpoint

### Network Check
- [ ] Docker container can reach Signal servers
- [ ] No firewall blocking outbound HTTPS (port 443)
- [ ] DNS resolution working for Signal domains
- [ ] Local REST API accessible (port 8080)

### Code Check
- [ ] Imports are correct
- [ ] API usage matches documentation
- [ ] Error handling implemented
- [ ] Logging enabled for debugging

### Production Check
- [ ] Health checks passing
- [ ] Metrics being collected
- [ ] Logs being written
- [ ] Alerts configured
- [ ] Backup procedures tested

## Getting Help

If you're still experiencing issues after following this guide:

1. **Check the logs** - Enable debug logging and examine the output
2. **Search existing issues** - Check the [GitHub issues](https://github.com/cornellsh/signal-client/issues)
3. **Create a minimal reproduction** - Isolate the problem to the smallest possible code
4. **Gather diagnostic information**:
   ```bash
   # System information
   uname -a
   python --version
   pip list | grep signal
   docker --version
   
   # Signal Client specific
   curl -s http://localhost:8080/v1/about
   curl -s http://localhost:8080/v1/accounts
   ls -la ~/.local/share/signal-api/
   ```
5. **Open an issue** with all diagnostic information and steps to reproduce

---

**Related Documentation:**
- [Security Guide](production_secrets.md) - Credential and security troubleshooting
- [Operations](operations.md) - Production deployment issues
- [API Reference](api-reference.md) - Method signatures and error types