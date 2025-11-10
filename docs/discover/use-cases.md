# Use Cases

| Scenario | Why signal-client helps |
| --- | --- |
| Support bots | Async handlers keep chatops responsive while retry logic avoids message loss. |
| Monitoring | Infrastructure adapters stream alerts directly into Signal groups with structured logging. |
| Workflows | Command layer exposes reusable verbs so operations teams automate deploys or runbooks. |

Use cases generally follow this lifecycle:

1. **Ingest** Signal events (webhooks or polling).
2. **Route** through the bot orchestrator and dependency injection containers.
3. **Execute** commands with typed inputs/outputs.
4. **Respond** via infrastructure adapters with audit logging.

See [recipes](../bots/guides/recipes.md) for concrete implementations.
