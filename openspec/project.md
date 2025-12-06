# Project Context

## Purpose
This project, `signal-client`, is an asynchronous Python framework for building bots on the Signal messaging platform. It acts as a client to the `signal-cli-rest-api`, consuming a websocket stream of messages, processing them through a resilient worker-based architecture, and providing a high-level API for interacting with Signal.

## Tech Stack
- **Language:** Python (3.9+) with a fully `asyncio`-based architecture.
- **Package Management:** `poetry` for dependency management and packaging.
- **Core Libraries:**
    - `aiohttp` and `websockets`: For REST API communication and the websocket message stream.
    - `pydantic` & `pydantic-settings`: For robust configuration and data modeling.
    - `structlog`: For structured, context-aware logging.
    - `aiosqlite` & `redis`: For persistent queuing and storage backends.
    - `prometheus-client`: For exposing application metrics.
- **Testing:**
    - `pytest`: Core testing framework.
    - `pytest-asyncio`: For testing asynchronous code.
    - `pytest-cov`: For code coverage measurement.
- **Linting & Formatting:**
    - `ruff`: For high-performance linting and code formatting.
    - `mypy`: For static type checking.
    - `bandit`: For security analysis.

## Project Conventions

### Code Style
- **Formatting:** Code is formatted with `ruff format`.
- **Linting:** `ruff check` is used to enforce a wide range of static analysis rules, configured in `pyproject.toml`.
- **Typing:** Strict static typing is enforced using `mypy`. All new code should be fully type-annotated.
- **Logging:** Use `structlog` for all logging; the standard `logging` library is banned via a lint rule.
- **Pre-commit:** Local quality checks are enforced via `pre-commit` hooks, which run `ruff`, `mypy`, and `bandit`.

### Architecture Patterns
- **Layered Architecture:** The application is organized into distinct layers:
    - `app.py`: The composition root, wiring all components together.
    - `infrastructure/`: Contains low-level clients for APIs and storage.
    - `runtime/`: Core message processing logic, including the websocket listener, worker pool, and command router.
    - `services/`: Higher-level application services.
    - `observability/`: Logging and metrics configuration.
- **Message Processing:** Incoming messages are received by a single listener, enqueued with an explicit backpressure policy, and fanned out to a pool of workers for concurrent processing.
- **Resiliency:** A Dead Letter Queue (DLQ) is used to handle message processing failures with exponential backoff for retries. API clients have built-in retry and circuit breaker logic.
- **Command Dispatch:** Bot commands are implemented as functions decorated with `@command` and are registered with a central router.

### Testing Strategy
- **Framework:** `pytest` is used for all tests.
- **Structure:** Tests are organized into `unit` and `integration` suites within the `tests/` directory.
- **CI Pipeline:** The CI workflow on GitHub Actions runs a comprehensive suite of checks on every push, including linting, type checking, security scans (`bandit`, `pip-audit`), and all tests.
- **Coverage:** Code coverage is tracked to ensure test quality.

### Git Workflow
- **Branching:** All work is done on feature branches and merged into `main` via Pull Requests.
- **CI/CD:** A GitHub Actions workflow (`.github/workflows/ci.yml`) automatically runs all quality gates.
- **Versioning:** `python-semantic-release` is used to automate versioning, changelog generation, and PyPI publishing based on conventional commit messages.

## Domain Context
- The project is a client for the Signal messaging protocol and depends on the concepts of that domain: users (identified by phone number), groups, messages, attachments, reactions, mentions, etc.
- It does not interact with Signal directly but through the `bbernhard/signal-cli-rest-api` service, which must be running and configured.
- The project includes an `audit-api.py` script to check its client implementation for parity with the upstream service's OpenAPI/Swagger specification.

## Important Constraints
- **External Service Dependency:** A running instance of `bbernhard/signal-cli-rest-api` is required for the application to function.
- **No Message History:** The upstream API does not provide access to message history. The client is responsible for its own persistence if historical data is needed.
- **Profile Limitations:** The API only supports updating profiles, not fetching them.

## External Dependencies
- **Primary Dependency:** The `bbernhard/signal-cli-rest-api` service, typically run as a Docker container. This service provides both the REST API and the websocket stream that `signal-client` consumes.
