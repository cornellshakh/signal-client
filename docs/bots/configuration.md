# Configuration

Configuration flows through `signal_client.context.settings` so deployments can override values without touching code.

## Environments

| Variable | Purpose |
| --- | --- |
| `SIGNAL_CLIENT_API_TOKEN` | Authenticates outbound requests. |
| `SIGNAL_CLIENT_WEBHOOK` | Source endpoint for inbound events. |
| `SIGNAL_CLIENT_LOG_LEVEL` | Overrides default logging verbosity. |

Store secrets in environment variables or `.env` files ignored by Git.

## Loading Settings

```python
from signal_client.context import settings

def build_bot():
    token = settings.api.token
    region = settings.runtime.region
    ...
```

## Deployment Targets

- Signal Cloud (managed) — configure via control plane, mount secrets.
- Bring Your Own Infrastructure — set env vars, reuse DI containers, run `python -m signal_client.compatibility --strict` before deploying.

Add configuration matrices using `table-reader` when options grow.
