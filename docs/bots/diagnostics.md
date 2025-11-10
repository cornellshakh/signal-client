# Diagnostics

Use these tools to inspect a live bot.

## Compatibility Checker

```bash
python -m signal_client.compatibility --strict
```

Compares runtime contracts to `cli_rest_api_swagger.json` and fails on drift.

## Health Commands

- `poetry run python -m signal_client.command.dump_state`
- `poetry run python -m signal_client.command.list_handlers`

## Troubleshooting Flow

1. Check health commands.
2. Inspect structured logs (see [Observability](observability.md)).
3. Run targeted tests (`pytest -k <feature>`).
4. Escalate to `tests/test_performance.py` when race conditions only repro under load.

Extend this page with codexec snippets once dedicated diagnostics APIs land.
