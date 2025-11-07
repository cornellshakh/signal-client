# Signal Client Docs

> Narrative-friendly Signal automations with production guardrails and observability baked in.

[Build your first bot](quickstart.md){ .md-button .md-button--primary }
[Explore the runtime](feature-tour.md){ .md-button }

## Choose your path

### Just browsing?

- [Overview](overview.md) — what Signal Client does and how it compares to rolling your own runtime.
- [Use Cases](use-cases.md) — inspiration drawn from customer ops, notification pipelines, and assistants.
- [Feature Tour](feature-tour.md) — the runtime layers explained with diagrams.

### Ready to build?

1. [Quickstart](quickstart.md) — link `signal-cli-rest-api`, install the package, and ship your first command.
2. [Architecture](architecture.md) — understand the worker pipeline, queueing model, and dependency injection layout.
3. [Configuration](configuration.md) — tune concurrency, back-pressure strategies, and storage adapters.
4. [Observability](observability.md) — wire metrics, structured logging, and compatibility checks.
5. [Operations](operations.md) — runbooks for scaling, DLQ replay, and controlled releases.
6. [API Reference](api-reference.md) — deep dive into classes, CLI tools, and helper utilities.

### Need guidance?

- [Writing Async Commands](guides/writing-async-commands.md) — patterns for non-blocking command code.
- [Coding Standards](coding_standards.md) — conventions when contributing.
- [Production Secrets](production_secrets.md) — how to secure credentials across environments.

!!! tip "Stay in the loop"
    Watch the [GitHub repository](https://github.com/cornellsh/signal-client) for release notes and roadmap discussions.

Happy building! If you get stuck, open a discussion or drop by the issue tracker—maintainers are eager to help.
