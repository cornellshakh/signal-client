---
title: Operations
summary: Runbooks for keeping Signal Client healthy in production.
order: 14
---

## Release guard

The release guard prevents risky deployments by validating system health before allowing updates.

### Upgrade checklist

1. `release-guard --check` — exit code must be zero before deploying.
2. Deploy new containers with rolling strategy; keep at least one worker on the previous version.
3. Monitor `signal_client_latency_seconds` and DLQ counters during rollout.
4. Rotate workers back if latency doubles or DLQ growth exceeds baseline.

!!! note "Plan maintenance windows"
    Signal network limits high-rate device reconnects. Schedule upgrades during low traffic to avoid reconnect storms.

## Incident response

/// details | Bridge connectivity issues
1. Confirm REST bridge container is healthy; restart if unresponsive.
2. Check signal-cli connectivity and device linking status.
3. If the device was unlinked, re-run the [Quickstart](quickstart.md#step-3-link-your-signal-device) flow.
///

/// details | Message backlog
1. Inspect the DLQ: `inspect-dlq --limit 20`.
2. Review failed messages and identify patterns in failures.
3. Consider scaling workers temporarily or fixing underlying issues.
///

/// details | Configuration drift
1. Review environment variables and configuration files.
2. Reconcile differences, then lock configuration via your secret store.
3. Run `release-guard --check` before re-enabling automation.
///

!!! danger "Pause automation when reprocessing"
    Disable cron jobs and webhook ingestion before replaying the DLQ, otherwise customers may receive duplicate replies.

## Scaling strategy

| Situation | Action |
| --- | --- |
| Gradual volume increase | Increase worker count via `WORKER_CONCURRENCY` or replica count. |
| Short-term surge | Queue jobs in Redis, enable rate limiting per command, drain after peak. |
| Sustained high demand | Shard workloads by Signal number across multiple linked devices. |

> **Next step** · Explore the command API in [API Reference](api-reference.md) or continue with [Guides](guides/writing-async-commands.md).
