# Overview

!!! info "Who should read this"
    Start here if you are evaluating Signal Client for a new automation project or want a high-level tour before diving into the technical guides.

Signal Client is an async runtime that helps you ship reliable Signal automations on top of [`signal-cli-rest-api`](https://github.com/bbernhard/signal-cli-rest-api) without rebuilding the operational foundations yourself.

## Why it exists

- **Resilience by default:** Queue management, bounded worker pools, rate limiting, and dead-letter workflows keep automations healthy under load.
- **Developer ergonomics:** Typed contexts, middleware hooks, and composable commands let you focus on the behavior, not plumbing.
- **Operational confidence:** Compatibility guards, structured logs, Prometheus metrics, and release checks reduce surprises in production.

## Signal Client at a glance

| Layer | Responsibility | Key docs |
| --- | --- | --- |
| Application | Register commands, inject dependencies, coordinate lifecycle | [Feature Tour](./feature-tour.md) |
| Core services | Move messages through workers, apply rate limits, handle retries | [Architecture](./architecture.md) |
| Infrastructure | WebSocket client, REST calls, storage adapters, schemas | [API Reference](./api-reference.md) |

## What’s included

- Command routing with string or regex triggers and typed `Context` helpers.
- Middleware system for authentication, logging, and feature flags.
- Metrics and logging instrumentation that surfaces queue depth, latency, and circuit-breaker status.
- Release guardrails that enforce the supported dependency matrix before code ships.
- Tooling around DLQ inspection, replay, and safe upgrade guidance.

## Why not just use `signal-cli-rest-api` directly?

| Without Signal Client | With Signal Client |
| --- | --- |
| Manually handle WebSocket reconnects and message parsing. | Reconnect and parsing logic handled inside the runtime with test coverage. |
| Build your own middleware, worker pools, and back-pressure strategies. | Tuned worker manager with configurable concurrency and queue limits out of the box. |
| Add metrics and logging instrumentation from scratch. | Prometheus metrics and structured logs ready to wire into dashboards. |
| Enforce dependency compatibility via release checklists. | Automated compatibility guard blocks unsupported versions at startup. |

## Where to go next

- Want real-world scenarios? Visit [Use Cases](./use-cases.md).
- Ready to explore internals? Jump into the [Feature Tour](./feature-tour.md) and [Architecture](./architecture.md).
- Prefer to build immediately? Follow the [Quickstart](./quickstart.md).
