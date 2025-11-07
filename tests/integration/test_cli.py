from __future__ import annotations

import asyncio
import json

import pytest

from signal_client.cli import inspect_dlq
from signal_client.config import Settings
from signal_client.container import Container


def _build_settings_override(
    container: Container, overrides: dict[str, str]
) -> Container:
    settings = Settings.from_sources(config=overrides)
    container.settings.override(settings)
    return container


@pytest.fixture(autouse=True)
def override_container_settings(monkeypatch):
    container = Container()
    _build_settings_override(
        container,
        {
            "phone_number": "+1234567890",
            "signal_service": "localhost:8080",
            "base_url": "http://localhost:8080",
            "storage_type": "sqlite",
            "sqlite_database": ":memory:",
        },
    )

    monkeypatch.setattr("signal_client.cli.Container", lambda: container)

    yield container

    container.shutdown_resources()


def test_inspect_dlq_outputs_messages(capfd, override_container_settings):
    container = override_container_settings
    dlq = container.services_container.dead_letter_queue()

    async def seed_dlq():
        await dlq.send({"id": "123", "body": "hello"})

    asyncio.run(seed_dlq())

    inspect_dlq()
    captured = capfd.readouterr()
    output = captured.out.strip().splitlines()
    assert output
    start_idx = next((i for i, line in enumerate(output) if line.startswith("[")), None)
    assert start_idx is not None, "Expected JSON output from inspect_dlq"
    json_payload = "\n".join(output[start_idx:])
    data = json.loads(json_payload)
    assert data[0]["message"]["body"] == "hello"
