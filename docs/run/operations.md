# Operations Runbook

Use this checklist when promoting bots to production.

- [ ] Secrets present in target environment
- [ ] `python -m signal_client.compatibility --strict` passes
- [ ] Monitoring dashboards linked (logs, metrics)
- [ ] Rollback procedure documented

## Deployments

```bash
poetry build
poetry run release_guard --target=prod
```

## Incident Response

1. Confirm alert in Signal group.
2. Check logs/metrics for anomalies.
3. Trigger diagnostics script if required.
4. Escalate per team rotation.

Add `pymdownx.tasklist` progress markers during rehearsals.
