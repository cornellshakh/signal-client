# Coding Standards

- Follow Conventional Commits (`fix:`, `chore:`, `docs:`).
- Use explicit typing throughout `src/signal_client`.
- Keep modules snake_case, classes PascalCase, and use Dependency Injector containers.
- Logging goes through `structlog`.
- Async handlers embrace `async`/`await`; avoid blocking operations.

Lint/type/test before opening a PR:

{{ dev_command_list() }}
