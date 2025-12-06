# Brand and Voice Guide

**Audience**: Python developers who want a dependable, async-first way to build Signal bots using `signal-cli-rest-api`.

**Positioning**: A Signal bot framework that wraps `signal-cli-rest-api` with resilient runtime primitives. Not affiliated with Signal Messenger.

**Tone**: Practical, concise, confident. Prefer direct verbs over hype. Explain safety and resiliency briefly; avoid marketing fluff.

**Word bank** (lean toward): async, resilient, backpressure, typed, bot runtime, Signal bot, community, open source, production-minded.

**Words to avoid**: “official Signal client,” “sealed/enterprise,” “magic,” “webhook-only,” “unsupported hacks.”

**Style cues**:
- Lead with the problem solved (build bots faster, handle retries/backpressure safely).
- Name `signal-cli-rest-api` explicitly and link when relevant.
- Mention that PII redaction is on by default.
- Keep sentences short; favor bullets over paragraphs for setup steps.
- Invite contributions with concrete next steps (open issues, good-first-issues, docs edits).

**Tagline**: “Async Python framework for resilient Signal bots”

**Elevator pitch (2–3 sentences)**: “signal-client is a async framework for Signal bots on top of `signal-cli-rest-api`. It ships with backpressure-aware ingestion, typed helpers for replies/reactions/attachments, and resilience features like durable queues and circuit breakers. Defaults favor safety and PII redaction so you can run bots in production with less glue code.”
