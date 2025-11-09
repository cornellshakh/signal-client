---
title: Feature Tour
summary: Explore the runtime capabilities before diving into code.
order: 3
---

## Feature highlights

/// tab | Messaging
- +heroicons:paper-airplane+ Send text, media, stories, and reactions with a single command API.
- Payload helpers serialize attachments, mentions, and group references safely.
- Built-in throttling adheres to Signal network expectations.
///

/// tab | Reliability
- +heroicons:lifebuoy+ Retry orchestration with exponential backoff and persistent DLQ.
- Circuit breakers wrap upstream dependencies to prevent cascading failures.
- Release guard verifies configuration drift before promoting to production.
///

/// tab | Observability
- +heroicons:chart-bar+ Prometheus counters, histograms, and RED metrics emitted per command.
- Structured logs route through structlog with correlation IDs.
- Compatibility guard ensures your linked device stays healthy.
///

## Operational tooling

- [Release guard](operations.md#release-guard) blocks risky deploys without manual dashboards.
- [Metrics](observability.md#metrics) surface latency, error codes, and attachment throughput.
- [CLI utilities](quickstart.md#step-5-validate-your-setup) bootstrap device linking, message sending, and troubleshooting.

!!! info "Want a deeper look?"
    Walk through the [Architecture](architecture.md) page for diagrams, component responsibilities, and deployment patterns.
