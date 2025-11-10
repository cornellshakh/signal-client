# Feature Tour

## Runtime Modules

- `signal_client.bot` — Orchestrates lifecycle hooks, retries, and scheduling.
- `signal_client.command` — Defines command schemas, validation, and async execution helpers.
- `signal_client.context` — Settings, dependency injection containers, and environment helpers.
- `signal_client.infrastructure` — Transports, persistence, and compatibility tools.

## Tooling

??? tip "Developer experience"
    - `poetry run ruff check .`
    - `poetry run black --check src tests`
    - `poetry run mypy src`

??? info "Testing"
    Use `poetry run pytest-safe -n auto --cov=signal_client` for the full sweep or `pytest -m \"not performance\"` to iterate quickly.

## Visual Index

Excalidraw sources live in `excalidraw/`. Export diagrams (for example, `key-management.json`) to PNG/SVG and drop them into `docs/assets/` for Lightbox embeds as they become available.
