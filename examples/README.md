# signal-client examples

Requires `SIGNAL_PHONE_NUMBER`, `SIGNAL_SERVICE_URL`, and `SIGNAL_API_URL` in the environment (plus `REDIS_HOST`/`REDIS_PORT` when using the Redis storage example).

- `basic_bot.py`: minimal ping bot with the `SignalClient` lifecycle.
- `context_helpers.py`: replies, typing indicators, reactions, attachments, mentions, and `context.lock`.
- `routing_and_middleware.py`: literal + regex triggers, whitelisting, and middleware hooks.
- `config_resiliency_and_metrics.py`: override settings, tune backpressure/worker pool, swap storage, and expose Prometheus metrics.
- `api_clients_and_dlq.py`: call REST clients from a command (contacts/history/groups) and one-shot DLQ replay via CLI.
