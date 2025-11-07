# Feature Tour

!!! info "Who should read this"
    Skim this page when you want a guided tour of the runtime layers before diving into detailed architecture and configuration docs.

Signal Client is organised into three layers that work together to deliver resilient automations. Use this tour to orient yourself and discover which components to customise.

## 1. Application surface

- **SignalClient container:** Manages lifecycle, dependency injection, and startup validation.
- **Commands:** Plain Python classes with `triggers` and async `handle` methods that receive a typed `Context`.
- **Middleware:** Optional before/after hooks for cross-cutting concerns such as authentication, logging, or feature gating.
- **Configuration helpers:** Pydantic-backed settings validate and document everything the runtime needs at launch.

**Read next:** [Quickstart](./quickstart.md) for a full command walkthrough.

## 2. Core services

- **MessageService:** Decodes incoming payloads, enriches metadata, and routes messages to the worker pool.
- **WorkerPoolManager:** Coordinates bounded async workers, back-pressure policies, and graceful shutdown.
- **RateLimiter & CircuitBreaker:** Protect upstream services and back off when resources fail or spike.
- **DeadLetterQueue:** Captures failed messages with retry metadata, exposes CLI tools for inspection and replay.

**Dive deeper:** [Architecture](./architecture.md) visualises how these services interact during steady state and failure modes.

## 3. Infrastructure adapters

- **WebSocket client:** Handles reconnect logic, heartbeats, and message framing from `signal-cli-rest-api`.
- **REST clients:** Wrap JSON-RPC endpoints in typed calls with observability hooks.
- **Storage adapters:** Plug in Redis or other persistence layers to move DLQ data and rate-limit tokens off-process.
- **Schemas:** Pydantic models standardise payloads and guard against breaking API changes.

**Reference material:** [API Reference](./api-reference.md) covers each adapter with method-level documentation.

## Visual overview

```
[ Signal CLI REST API ] → WebSocket Client → Message Service → Worker Pool
                                         ↘ Rate Limiter ↘ Circuit Breaker
Workers ↔ Commands ↔ Middleware ↔ Contexts
         ↘ Dead Letter Queue ↘ Metrics & Logs
```

Download a high-resolution architecture diagram from the [Architecture](./architecture.md) page.

## Try it yourself

- Build a pilot bot via the [Quickstart](./quickstart.md).
- Instrument metrics following the [Observability](./observability.md) guide.
- Stress-test your workload with the [Operations](./operations.md) playbooks.
