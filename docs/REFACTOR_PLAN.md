# Refactor Blueprint: signal-client (senior-grade, clear, KISS)

## Goals and Constraints
- Keep all existing functionality, observability, and test coverage (118 tests) intact; refactor for readability, predictability, and maintainability.
- Aim for senior-level clarity: explicit lifecycles, strong typing, disciplined naming, minimal indirection, but no loss of capability.
- Preserve pipeline semantics (websocket → backpressured queue → worker pool → command dispatch → REST clients) and configuration via env/.env.
- Avoid public API breakage unless justified; if unavoidable, document migration steps and keep surface area stable.

## Current Pain Points (quick audit)
- DI sprawl: `container.py` uses nested dependency_injector containers for a small graph, obscuring lifecycles and making debugging harder.
- Configuration uses multiple mixins plus custom env-merging helpers, hiding the minimal required envs and muddying validation.
- Command dispatch over-abstracted: trigger compilation loses registration order intent; middleware wiring is split across manager/state.
- Message ingestion/backpressure spreads across multiple helpers with implicit defaults; unused flags and implicit drop-oldest behavior reduce readability.
- Naming/layout is uneven (`services` vs `infrastructure`, `entities.py` for DTOs, Typer CLI for one DLQ command); module roles are not obvious at a glance.
- Observability is split (`metrics.py` + tiny `metrics_server.py`, structlog guard in `bot.py`) without a cohesive observability surface.

## Target Shape (high level)
- Explicit application composition (no DI framework): a small builder that wires config → websocket listener → queue/backpressure → worker pool/router → API clients.
- Intentional package layout:
  - `signal_client/config.py` (single Settings model)
  - `signal_client/app.py` (builder + lifecycle)
  - `signal_client/runtime/` (listener, backpressure policy, worker pool, command router, middleware)
  - `signal_client/api/` (REST clients)
  - `signal_client/storage/` (sqlite/redis + DLQ helpers)
  - `signal_client/observability/` (metrics, exporter, logging bootstrap)
- Command triggers respect registration order; regex commands are explicit; middleware chain is simple and transparent.

## Task List (execution-ready)

### Baseline and Safety
- [x] Confirm current baseline with `poetry run pytest-safe -n auto --cov=signal_client`; baseline green on Python 3.13.7 (118 tests).
- [ ] Track any public-surface adjustments and update README/examples when they occur.

### Configuration Simplification (clear, typed)
- [x] Replace multi-mixin `Settings` and custom env-merging helpers with a single pydantic model that directly maps required envs (`SIGNAL_PHONE_NUMBER`, `SIGNAL_SERVICE_URL`, `SIGNAL_API_URL`) and grouped options (queue, dlq, api, rate limiter, circuit breaker, storage).
- [x] Remove `_temporarily_remove_env`, `_field_aliases`, etc.; rely on standard pydantic settings (`model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)`).
- [x] Keep validation messages concise and precise; adjust tests to match the new, clearer semantics.

### Composition Without dependency_injector
- [x] Replace `container.py` with `app.py` that constructs shared resources explicitly (aiohttp session, storage backend, API clients, queue, router, worker pool, websocket client).
- [x] Update `SignalClient` to use the new builder, with explicit start/shutdown handling (close websocket, drain queue, stop workers, close session/storage) and tight typing.
- [x] Refresh tests/mocks to target concrete components instead of providers.

### Runtime Pipeline Clarity
- [x] Move `MessageService` into `runtime/listener.py`; remove unused flags; expose backpressure policy explicitly (e.g., enum `fail_fast` vs `drop_oldest`) and document defaults.
- [x] Split routing from execution: introduce `CommandRouter` (ordered triggers + regex list) and a lean `worker_pool.py` that pulls from the queue, routes, applies middleware, and records metrics.
- [x] Keep `QueuedMessage` in `runtime/models.py`; ensure latency/depth metrics remain but simplify log keys and variable names for readability.

### Storage and DLQ
- [ ] Move storage modules under `signal_client/storage/` (`base.py`, `sqlite.py`, `redis.py`); keep the interface minimal (`append`, `read_all`, `delete_all`, `close`).
- [ ] Simplify `DeadLetterQueue`: keep backoff and metrics, reduce logging noise, and store raw payload + retry count clearly.
- [ ] Update CLI/tests to new paths; maintain behavior parity.

### Observability Cohesion
- [ ] Consolidate metrics and exporter into `observability/metrics.py` with `start_metrics_server(port, addr, registry=None)` and `render_metrics()`; keep Prometheus names stable.
- [ ] Move structlog bootstrap into `observability/logging.py`; default to concise, JSON-optional output while respecting external configuration.
- [ ] Document metrics usage and defaults in README.

### CLI and Tooling
- [ ] Replace the Typer CLI with a minimal, dependency-free CLI (`python -m signal_client.cli`) that supports `dlq inspect` (and optional `dlq purge`) without global containers.
- [ ] Re-evaluate `compatibility.py`: keep as a simple optional guard or drop if redundant; ensure tests reflect the chosen path.
- [ ] Leave `release_guard.py` intact unless tests require adjustments.

### Naming and Documentation Pass
- [ ] Rename generic modules (`entities.py`, `services/models.py`) to clearer equivalents (`context_deps.py`, `runtime/models.py`) and update imports.
- [ ] Refresh README Quickstart to reflect the new builder/CLI and include a brief architecture outline matching the package layout.
- [ ] Keep docstrings where logic is non-obvious (backpressure policy, circuit breaker thresholds); keep them concise and action-oriented.

### Verification
- [ ] Run quality gate: `poetry run ruff check .`; `poetry run black --check src tests`; `poetry run mypy src`; `poetry run pytest-safe -n auto --cov=signal_client`.
- [ ] Note any intentional breaking changes in README or CHANGELOG with migration guidance.

## Notes for the Implementing Agent
- Work incrementally: simplify config and composition first, then move modules; avoid broad file moves until lifecycles are solid.
- When moving modules, update imports in code and tests in the same change to prevent transient breakage.
- Preserve API client signatures and behavior; refactor is about clarity, not feature removal.
- Prefer clear helpers over cleverness; keep types and lifecycles explicit; retain observability hooks (metrics/logging) while making them easier to follow.

## Current Pain Points (quick audit)
- DI sprawl: `container.py` wires three nested containers via dependency_injector for a small graph, making call sites hard to follow and unfriendly to debugging.
- Configuration is split across multiple `BaseSettings` subclasses plus custom alias/merge helpers (`Settings.from_sources`, `_temporarily_remove_env`), obscuring the minimal required envs.
- Command dispatch is over-abstracted: `WorkerPoolManager` compiles sorted trigger regexes (order loses registration intent), keeps duplicate registries, and mixes middleware concerns.
- Message ingestion/backpressure is spread across `MessageService`, `DeadLetterQueue`, and queue metrics; `_started` flags are unused; drop-oldest semantics are implicit.
- Naming/layout is inconsistent: `services` vs `infrastructure`, `entities.py` for simple data holders, `compatibility.py` guard, and a Typer-based CLI for a single DLQ inspect command.
- Metrics exposure is hidden behind a tiny `metrics_server.py` wrapper instead of a clear `observability` module with documented lifecycle.

## Target Shape (high level)
- Single lightweight application builder (no dependency_injector) that wires config → websocket listener → queue → worker pool → command router → REST clients.
- Flat, intention-revealing package layout:
  - `signal_client/config.py` (simple Settings)
  - `signal_client/app.py` (builder/wiring; replaces containers)
  - `signal_client/runtime/` (listener, queue/backpressure, worker pool, command router, middleware hooks)
  - `signal_client/api/` (REST clients)
  - `signal_client/storage/` (sqlite/redis + DLQ helpers)
  - `signal_client/observability/` (metrics, optional HTTP exporter, structlog setup)
- Command triggers preserve registration order by default; regex commands explicit; middleware pluggable but minimal.

## Task List (execution-ready)

### Baseline and Safety
- [x] Snapshot current behavior: run `poetry run pytest-safe -n auto --cov=signal_client` to confirm the starting point (record failures if any); baseline green on Python 3.13.7 (118 tests).
- [ ] Document any public API changes as you implement tasks; update README examples accordingly.

### Simplify Configuration
- [x] Replace the multi-mixin `Settings` + helper functions with a single `Settings` dataclass/pydantic model that directly maps required env vars (`SIGNAL_PHONE_NUMBER`, `SIGNAL_SERVICE_URL`, `SIGNAL_API_URL`) and simple option groups (queue, dlq, api, rate limiter, circuit breaker, storage).
- [x] Remove `_temporarily_remove_env`, `_field_aliases`, etc.; use `model_config = SettingsConfigDict(env_file=".env", extra="ignore")` and straightforward defaults.
- [x] Update tests that expect alias/merge behaviors to the new simpler semantics; keep validation messages clear and short.

### Remove dependency_injector
- [x] Delete `container.py` and associated container classes; introduce `app.py` (or similar) with pure-Python factories that build the handful of shared objects (session, storage, clients, queue, router, workers).
- [x] Update `SignalClient` to own/wire components directly via the new builder; ensure lifecycle hooks (`start`, `shutdown`, async context manager) still close websocket, queue, workers, HTTP session, and storage.
- [x] Adjust tests/mocks to target the new builder and concrete types instead of container providers.

### Clarify Runtime Pipeline
- [x] Move `MessageService` into `runtime/listener.py`; strip unused `_started`, make backpressure policy explicit via a small strategy enum (`fail_fast` vs `drop_oldest`).
- [x] Collapse `WorkerPoolManager` + `Worker` into a clearer `worker_pool.py` with: ordered trigger matching (respect registration order), explicit regex command list, and simple middleware chain (no provider wiring).
- [x] Introduce a `CommandRouter` responsible solely for trigger registration/matching; keep it deterministic and easy to unit test.
- [x] Keep `QueuedMessage` as a tiny dataclass in `runtime/models.py`; ensure latency metrics remain, but simplify names/log keys.

### Streamline Storage and DLQ
- [ ] Rehome storage modules to `signal_client/storage/` with `base.py`, `sqlite.py`, `redis.py`; ensure interfaces are minimal (`append`, `read_all`, `delete_all`, `close`).
- [ ] Simplify `DeadLetterQueue`: store raw payload + retry count; keep backoff helper but trim logging noise; ensure metrics updates remain.
- [ ] Update CLI and tests to reflect new module paths.

### Observability Cleanup
- [ ] Consolidate `metrics.py` and `metrics_server.py` into `observability/metrics.py`; expose a single `start_metrics_server(port, addr, registry=None)` and `render_metrics()`.
- [ ] Move structlog bootstrapper from `bot.py` into `observability/logging.py`; keep the guard to respect external configuration but make defaults shorter (no JSON renderer unless requested).
- [ ] Document metrics usage in README (one short section with code snippet and default bind address).

### CLI and Tooling
- [ ] Replace Typer-based CLI with a minimal `python -m signal_client.cli` that supports `dlq inspect` (and optionally `dlq purge`) via argparse or plain functions; avoid global container usage.
- [ ] Evaluate `compatibility.py` guard; either drop it or reduce to a single optional `check_supported_versions()` helper invoked only in CLI/dev paths.
- [ ] Ensure `release_guard.py` stays untouched unless tests require changes.

### Naming and Documentation Pass
- [ ] Rename generic modules (`entities.py`, `services/models.py`) to clearer counterparts (`context_deps.py`, `runtime/models.py`), updating imports.
- [ ] Update README Quickstart to reflect new builder/CLI, and include a short architecture diagram (bullet list) that mirrors the new package layout.
- [ ] Add inline docstrings where logic is non-obvious (backpressure policy, circuit breaker thresholds), keep them concise.

### Verification
- [ ] Run the quality gate: `poetry run ruff check .`, `poetry run black --check src tests`, `poetry run mypy src`, `poetry run pytest-safe -n auto --cov=signal_client`.
- [ ] Record any intentional breaking changes in a `CHANGELOG` entry or README note.

## Notes for the Implementing Agent
- Work incrementally: finish config simplification and DI removal before moving files to the new layout to keep diffs reviewable.
- When moving modules, update import paths in both code and tests in the same commit to avoid transient breakage.
- Keep API client method signatures intact unless there is a strong reason to change; the refactor is about structure/naming, not new features.
- Prefer small helper functions over classes when behavior is stateless; remove unnecessary indirection or caching that is not validated by tests.
