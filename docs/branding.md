# Branding and Naming Rationale

## Name
We keep the repository and package name **signal-client** for continuity and search parity with the published PyPI package, while explicitly positioning it as a *community Signal bot framework* (not the official Signal app). Alternative names considered: “Signal Bot Kit,” “Signal Bot Runtime,” and “Signal Async Bot.” We rejected them to avoid package rename churn and because “signal-client” already ranks for “Signal bot Python” searches.

## Differentiation
- Distinct from the official Signal apps and `signal-cli` tooling: we sit above `signal-cli-rest-api` as an async Python bot runtime with resiliency and typed helpers.
- Distinct from other community frameworks such as `filipre/signalbot` (micro-framework), `aaronetz/signal-bot` (Java), and `signal-bot-framework` on PyPI; our focus is resilient ingestion, backpressure, and production-minded defaults (PII redaction on, durable queues).

## Tagline
“Async Python framework for resilient Signal bots (community SDK, not the official Signal app).”

## Usage in public touchpoints
- README title + badges and first paragraph.
- Docs landing page intro paragraph.
- PyPI `description` and README long description.

## Contributor cues
Invite contributions through clear badges, “issues/PRs welcome” language in README, and consistent tone per `docs/brand_voice.md`.
