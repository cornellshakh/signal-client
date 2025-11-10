# Testing

Signal-client relies on `pytest`, `pytest-asyncio`, and `aresponses`.

## Required Commands

| Check | Command |
| --- | --- |
| Lint | `poetry run ruff check .` |
| Format | `poetry run black --check src tests` |
| Types | `poetry run mypy src` |
| Unit/Integration | `poetry run pytest-safe -n auto --cov=signal_client` |
| Quick Iteration | `pytest -m "not performance"` |

## Patterns

- Name tests `test_<subject>_<behavior>`.
- Keep fixtures deterministic—prefer `aresponses` over sleeps.
- Cover retry logic and scheduling with regression tests.
- Use the `performance` marker only for long-running stress jobs.

## Templates

```python
import pytest

@pytest.mark.asyncio
async def test_command_echoes_text(bot_client, signal_event):
    response = await bot_client.handle(signal_event)
    assert response.payload == signal_event.payload
```

Document integration suites in `tests/integration/`; load tests live in `tests/test_performance.py`.
