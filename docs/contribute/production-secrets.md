# Production Secrets

- Store Signal credentials and webhooks in environment variables or `.env` files ignored by Git.
- Access configuration via `signal_client.context.settings` to keep overrides deployable.
- Rotate tokens regularly; document process in runbooks.
- Never embed secrets in fixtures, docs, or screenshots.

When touching serialization, crypto, or persistence, run:

```bash
poetry run bandit -c bandit.yaml -r src
```
