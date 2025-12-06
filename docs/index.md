# signal-client — Async Signal bot framework (community SDK, not official Signal)

Community-built async framework for Signal bots on top of `signal-cli-rest-api`. Provides websocket ingestion with backpressure, typed helpers for replies/attachments/reactions, and resilience primitives (durable queues, rate limiting, circuit breakers) so bots stay healthy. Defaults favor safety and PII redaction; contributors are welcome via issues and PRs.

## Highlights
- Websocket ingestion with a worker pool and backpressure controls.
- Structured logging with optional PII redaction.
- Typed context helpers for replies, reactions, attachments, and receipts.
- Resiliency primitives: rate limiting, circuit breakers, durable queues, and a DLQ.
- Prometheus metrics and optional health endpoints for operations.

## Quick links
- [Getting started](getting_started.md) — prerequisites, install, and a minimal bot.
- [Examples](examples.md) — runnable scripts for ping, reminders, and webhook relay.
- [Advanced usage](guides/advanced_usage.md) — middleware, context helpers, and locking.
- [Operations & deployment](guides/production_deployment.md) — configuration, storage, and observability.
- [Release & publishing](guides/release.md) — quality gates, packaging, and docs publishing.
- [Brand voice](brand_voice.md) — tone, word bank, and contributor copy guidance.
