# Production Deployment and Redis Configuration

This guide outlines best practices for deploying your Signal Client application to production environments, focusing on robustness, scalability, and security. A key component for high-performance and distributed deployments is Redis, which is used for caching, session management, and as a message broker.

---

## 1. Environment Setup

### Operating System
It's recommended to deploy on a Linux-based operating system (e.g., Ubuntu, Debian, CentOS) for optimal performance and compatibility.

### Python Environment
Use a virtual environment (e.g., `venv` or `conda`) to manage your project's dependencies and avoid conflicts with system-wide packages.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Dependency Management
Ensure all project dependencies are pinned to specific versions using `pip freeze > requirements.txt` to guarantee consistent deployments.

---

## 2. Redis Installation and Configuration

Redis is crucial for Signal Client's performance. Install it on your production server.

### Installation (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install redis-server
```

### Configuration (`/etc/redis/redis.conf`)

Edit the Redis configuration file to secure and optimize your instance:

- **Bind to Specific Interface:**
  ```
  bind 127.0.0.1 ::1
  ```
  Change `127.0.0.1` to your server's internal IP address if your application server is separate from the Redis server, and only allow connections from trusted sources.

- **Require Password (Strongly Recommended):**
  ```
  requirepass your_strong_redis_password
  ```
  Replace `your_strong_redis_password` with a strong, unique password.

- **Max Memory Policy:**
  ```
  maxmemory <size>mb
  maxmemory-policy allkeys-lru
  ```
  Configure `maxmemory` based on your server's RAM and set `maxmemory-policy` to `allkeys-lru` to evict least recently used keys when memory limits are reached.

- **Persistence (Optional but Recommended):**
  Enable RDB persistence for data durability:
  ```
  save 900 1
  save 300 10
  save 60 10000
  ```
  Or AOF persistence for better durability:
  ```
  appendonly yes
  ```

### Restart Redis

```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

---

## 3. Application Configuration for Redis

The Signal Client uses environment variables or a configuration file to connect to Redis.

### Environment Variables

Set the following environment variables in your production environment:

```bash
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_strong_redis_password
```

Adjust `REDIS_HOST` if Redis is running on a different server.

### Configuration File (e.g., `config.py`)

Alternatively, ensure your application's `config.py` (or equivalent) is set up to read these values, ideally from environment variables first, then fallback to secure defaults.

```python
# In signal_client/config.py (example)
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Example usage in your application
# import redis
# redis_client = redis.Redis(
#     host=REDIS_HOST,
#     port=REDIS_PORT,
#     db=REDIS_DB,
#     password=REDIS_PASSWORD
# )
```

---

## 4. Running the Application in Production

### Process Manager
Use a process manager like Gunicorn, PM2, or Systemd to run your application, manage worker processes, and ensure it restarts automatically if it crashes.

#### Example with Gunicorn

1. **Install Gunicorn:**
   ```bash
   pip install gunicorn
   ```

2. **Create a Gunicorn configuration file (e.g., `gunicorn_config.py`):**

   ```python
   # gunicorn_config.py
   bind = "0.0.0.0:8000"
   workers = 4  # Adjust based on your CPU cores (2-4 workers per core)
   worker_class = "uvicorn.workers.UvicornWorker" # If using ASGI (FastAPI, Starlette)
   timeout = 120
   keepalive = 5
   errorlog = "/var/log/gunicorn/error.log"
   accesslog = "/var/log/gunicorn/access.log"
   loglevel = "info"
   ```

3. **Run Gunicorn:**
   ```bash
   gunicorn your_application_module:app --config gunicorn_config.py
   ```
   Replace `your_application_module:app` with the actual path to your FastAPI/Starlette application instance.

### Reverse Proxy (Nginx/Apache)
Use a reverse proxy (e.g., Nginx or Apache) in front of your Gunicorn application to handle SSL termination, load balancing, and serve static files efficiently.

#### Example Nginx Configuration

```nginx
server {
    listen 80;
    server_name your_domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your_domain.com;

    ssl_certificate /etc/nginx/ssl/your_domain.com.crt;
    ssl_certificate_key /etc/nginx/ssl/your_domain.com.key;

    location / {
        proxy_pass http://127.0.0.1:8000; # Gunicorn listens on 8000
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 5. Logging and Monitoring

- **Centralized Logging:** Use a centralized logging solution (e.g., ELK Stack, Grafana Loki, Datadog) to aggregate logs from all application instances and Redis.
- **Monitoring:** Implement application and infrastructure monitoring to track performance, resource usage, and error rates. Prometheus and Grafana are excellent open-source options.

---

## 6. Security Considerations

- **Secrets Management:** Never hardcode sensitive information. Use environment variables, a secrets management service (e.g., HashiCorp Vault, AWS Secrets Manager), or a `.env` file (for local development only, *never* in production).
- **Firewall:** Configure your server's firewall (e.g., `ufw`, `firewalld`) to only allow necessary incoming connections (e.g., SSH, HTTP/S, Redis from application server).
- **Least Privilege:** Run your application with a dedicated, non-root user with minimal necessary permissions.
- **Regular Updates:** Keep your operating system, Python, Redis, and all dependencies updated to patch security vulnerabilities.
