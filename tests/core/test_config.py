"""Tests for the config module."""

from __future__ import annotations

import asyncio
import os
from typing import Any
from unittest import mock

import pytest

from signal_client import SignalClient
from signal_client.core.config import Settings
from signal_client.exceptions import ConfigurationError


def _assert_client_settings(
    client: SignalClient,
    *,
    phone_number: str,
    signal_service: str,
    worker_pool_size: int,
) -> None:
    """Assert client settings."""
    assert client.settings.phone_number == phone_number
    assert client.settings.signal_service == signal_service
    assert client.settings.worker_pool_size == worker_pool_size
    asyncio.run(client.shutdown())


def test_settings_load_from_env(mock_env_vars):
    """Test that settings are loaded correctly from environment variables."""
    settings = Settings.from_sources()
    assert settings.phone_number == "+1234567890"
    assert settings.signal_service == "http://localhost:8080"
    assert settings.base_url == "http://localhost:8080/v1"
    assert settings.worker_pool_size == 4  # Check default value
    assert settings.queue_put_timeout == 1.0
    assert settings.queue_drop_oldest_on_timeout is True


def test_settings_missing_required():
    """Test that a configuration error is raised when required settings are missing."""
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError) as exc_info:
            Settings.from_sources()
    message = str(exc_info.value)
    assert "SIGNAL_PHONE_NUMBER" in message
    assert "SIGNAL_SERVICE_URL" in message
    assert "SIGNAL_API_URL" in message


@pytest.mark.parametrize(
    ("config", "expected_phone", "expected_workers"),
    [
        (None, "+1234567890", 4),
        (
            {
                "phone_number": "+1111111111",
                "signal_service": "http://localhost:8080",
                "base_url": "http://localhost:8080",
                "worker_pool_size": 8,
            },
            "+1111111111",
            8,
        ),
    ],
)
def test_signal_client_init_with_env_variants(
    mock_env_vars,
    config: dict[str, Any] | None,
    expected_phone: str,
    expected_workers: int,
) -> None:
    """SignalClient picks up env vars and allows selective overrides."""
    client = SignalClient(config=config)
    _assert_client_settings(
        client,
        phone_number=expected_phone,
        signal_service="http://localhost:8080",
        worker_pool_size=expected_workers,
    )


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (None, None),
        (
            {
                "phone_number": "+2222222222",
                "signal_service": "ws://localhost:8081",
                "base_url": "http://localhost:8081",
                "worker_pool_size": 2,
            },
            {
                "phone_number": "+2222222222",
                "signal_service": "ws://localhost:8081",
                "worker_pool_size": 2,
            },
        ),
    ],
)
def test_signal_client_init_without_env(
    config: dict[str, Any] | None,
    expected: dict[str, Any] | None,
) -> None:
    """SignalClient either errors or relies entirely on provided config when env vars

    are absent.
    """
    with mock.patch.dict(os.environ, {}, clear=True):
        if expected is None:
            with pytest.raises(ConfigurationError):
                SignalClient(config=config)
            return

        client = SignalClient(config=config)
        _assert_client_settings(
            client,
            phone_number=expected["phone_number"],
            signal_service=expected["signal_service"],
            worker_pool_size=expected["worker_pool_size"],
        )


def test_settings_invalid_redis_configuration():
    """Test that invalid Redis configuration raises a ConfigurationError."""
    with mock.patch.dict(os.environ, {}, clear=True):
        config = {
            "phone_number": "+111",
            "signal_service": "localhost:9000",
            "base_url": "http://localhost:9000",
            "worker_pool_size": 1,
            "storage_type": "redis",
            "redis_host": "",
            "redis_port": 6379,
        }
        with pytest.raises(ConfigurationError, match="redis_host"):
            Settings.from_sources(config=config)


def test_settings_invalid_sqlite_configuration(mock_env_vars):
    """Test that invalid SQLite configuration raises a ConfigurationError."""
    config = {"storage_type": "sqlite", "sqlite_database": ""}
    with pytest.raises(ConfigurationError, match="sqlite_database"):
        Settings.from_sources(config=config)


def test_settings_invalid_config_overrides_report_missing_fields(mock_env_vars):
    """Test that invalid config overrides report missing fields."""
    config = {"phone_number": None}
    with pytest.raises(ConfigurationError, match="phone_number"):
        Settings.from_sources(config=config)
