# signal-client Guide (Codex CLI)

## Layout & Ownership
- Runtime code: `src/signal_client/` grouped by surface (`bot`, `command`, `context`, `infrastructure`); matching tests live in `tests/`, with integrations in `tests/integration/` and load checks in `tests/test_performance.py`.
- Docs/mkdocs content: `docs/`, `mkdocs.yml`, `macros/`; automation helpers reside in `scripts/` (every CLI entry exposes `main()`).
- Shared assets: `cli_rest_api_swagger.json` plus diagrams in `excalidraw/`.

## Dev Workflow
- `poetry install --sync` to prep the env.
- Lint/format: `poetry run ruff check .`, `poetry run black --check src tests`.
- Types/tests: `poetry run mypy src`, `poetry run pytest-safe -n auto --cov=signal_client`, quick loops with `pytest -m "not performance"`.
- Docs/build: `poetry run mkdocs serve`, `poetry build`.
- Security/compat: `poetry run bandit -c bandit.yaml -r src`, `python -m signal_client.compatibility --strict`.

## Coding Rules
- Python, 4-space indent, Black defaults; Ruff runs with `select = ["ALL"]`, so add targeted `# noqa` only with justification.
- Favor explicit typing and Dependency Injector wiring; avoid module singletons.
- Async handlers use `async`/`await`, logging via `structlog`, modules snake_case, classes PascalCase.

## Testing Expectations
- Use `pytest`, `pytest-asyncio`, `aresponses`; name tests `test_<subject>_<behavior>`.
- New behavior ⇒ unit tests plus integration coverage if messaging flows change; keep bot orchestration coverage >90%.
- Deterministic fixtures > sleeps; mark long soak jobs with `@pytest.mark.performance`.

## PR & Change Hygiene
- Conventional commits (`fix:`, `chore:`, `docs:` ...), ≤72 char subject, mention related issues (e.g., `Fixes #123`).
- PRs include user story links, schema/config migration notes, screenshots for docs/UI, and a “Test Plan” with exact commands run.
- Update `docs/` or changelog when touching APIs, CLI flags, or compatibility contracts.

## Secrets & Config
- Never hardcode credentials; load via env or `.env` ignored by Git using `signal_client.context.settings`.
- When altering serialization/crypto/persistence, run Bandit (above) and make sure REST compatibility matches `cli_rest_api_swagger.json`.
