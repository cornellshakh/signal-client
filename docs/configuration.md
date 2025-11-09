---
title: Configuration
summary: Configure Signal Client for development and production environments with environment variables and config files.
order: 12
---

# Configuration

Configure your Signal bot for different environments and deployment scenarios. Signal Client supports both environment variables and TOML configuration files.

## Environment Variables

The simplest way to configure Signal Client is through environment variables:

### Required Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `SIGNAL_CLIENT_NUMBER` | Your Signal phone number (E.164 format) | `+1234567890` |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SIGNAL_CLIENT_REST_URL` | `http://localhost:8080` | signal-cli REST API endpoint |
| `SIGNAL_CLIENT_SECRETS_DIR` | `~/.local/share/signal-api` | Signal credentials directory |
| `SIGNAL_CLIENT_CONFIG_PATH` | `~/.config/signal-client/config.toml` | Configuration file path |
| `SIGNAL_CLIENT_LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `SIGNAL_CLIENT_METRICS_PORT` | `9300` | Prometheus metrics port (0 to disable) |

### Development vs Production

/// tab | Development
```bash
# .env file for development
SIGNAL_CLIENT_NUMBER="+1234567890"
SIGNAL_CLIENT_REST_URL="http://localhost:8080"
SIGNAL_CLIENT_LOG_LEVEL="DEBUG"
SIGNAL_CLIENT_METRICS_PORT="0"
```
///

/// tab | Production
```bash
# Production environment variables
SIGNAL_CLIENT_NUMBER="+1234567890"
SIGNAL_CLIENT_REST_URL="https://signal-api.internal:8080"
SIGNAL_CLIENT_LOG_LEVEL="INFO"
SIGNAL_CLIENT_METRICS_PORT="9300"
SIGNAL_CLIENT_SECRETS_DIR="/run/secrets/signal"
```
///

!!! warning "Credential Security"
    - Never commit Signal credentials to version control
    - Use proper file permissions (600) for credential directories
    - Consider using secret management systems in production

## Configuration Files

For complex configurations, use TOML files instead of environment variables:

### Basic Configuration File

```toml
# ~/.config/signal-client/config.toml
[signal_client]
phone_number = "+1234567890"
rest_url = "http://localhost:8080"
secrets_dir = "/home/user/.local/share/signal-api"

[logging]
level = "INFO"
format = "json"  # or "text"

[worker]
pool_size = 4
queue_size = 200
retry_attempts = 3
retry_delay = 5.0

[rate_limiting]
enabled = true
max_messages_per_minute = 60
burst_size = 10
```

### Advanced Configuration

```toml
# Production configuration example
[signal_client]
phone_number = "+1234567890"
rest_url = "https://signal-api.internal:8080"
secrets_dir = "/run/secrets/signal"

[storage]
type = "redis"
url = "redis://redis-cluster:6379/0"
connection_pool_size = 10

[metrics]
enabled = true
port = 9300
path = "/metrics"

[security]
verify_ssl = true
timeout = 30.0
max_retries = 3

[worker]
pool_size = 8
queue_size = 500
retry_attempts = 5
retry_delay = 10.0
```

### Loading Configuration

```python
from signal_client.bot import SignalClient

# Load from default location
client = SignalClient()

# Load from specific file
client = SignalClient(config_path="/path/to/config.toml")

# Override with environment variables
# Environment variables take precedence over config file values
```

## Directory Structure

Signal Client requires access to Signal credentials managed by signal-cli:

```text
# Typical development setup
project-root/
├── bot.py                        # Your Signal bot application
├── .env                          # Environment variables (optional)
├── config.toml                   # Configuration file (optional)
└── ~/.local/share/signal-api/    # Signal credentials (created by signal-cli)
    ├── data/
    │   └── +1234567890.d/        # Your phone number data
    │       ├── identity-key
    │       ├── pre-keys/
    │       └── sessions/
    └── attachments/              # Attachment storage
```

### File Permissions

!!! warning "Secure Credential Storage"
    Signal credentials contain sensitive cryptographic keys:
    
    ```bash
    # Set proper permissions for credential directory
    chmod 700 ~/.local/share/signal-api/
    chmod 600 ~/.local/share/signal-api/data/+1234567890.d/*
    ```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  signal-bot:
    build: .
    environment:
      - SIGNAL_CLIENT_NUMBER=+1234567890
      - SIGNAL_CLIENT_REST_URL=http://signal-api:8080
    volumes:
      - signal-data:/app/signal-data
    depends_on:
      - signal-api

  signal-api:
    image: bbernhard/signal-cli-rest-api:latest
    ports:
      - "8080:8080"
    volumes:
      - signal-data:/home/.local/share/signal-cli

volumes:
  signal-data:
```

## Configuration Validation

Signal Client validates configuration on startup:

```python
from signal_client.config import validate_config
from signal_client.exceptions import ConfigurationError

try:
    config = validate_config()
    print("✅ Configuration is valid")
except ConfigurationError as e:
    print(f"❌ Configuration error: {e}")
    # Fix configuration and retry
```

### Common Configuration Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `Missing SIGNAL_CLIENT_NUMBER` | Phone number not set | Set environment variable or config file |
| `REST API unreachable` | signal-cli not running | Start signal-cli REST API container |
| `Device not linked` | Signal device not registered | Complete device linking process |
| `Permission denied` | Incorrect file permissions | Fix credential directory permissions |

!!! tip "Configuration Testing"
    Use the `release-guard` CLI tool to validate your configuration before deployment:
    
    ```bash
    release-guard --check-config
    release-guard --check-connectivity
    ```
