from __future__ import annotations

import asyncio
import os
from unittest import mock

import pytest

from signal_client.bot import SignalClient
from signal_client.config import Settings
from signal_client.exceptions import ConfigurationError


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


def test_signal_client_init_with_env(mock_env_vars):
    """Test SignalClient initialization with environment variables."""
    client = SignalClient()
    settings = client.container.settings()
    assert settings.phone_number == "+1234567890"
    assert settings.signal_service == "http://localhost:8080"
    asyncio.run(client.shutdown())


def test_signal_client_init_with_config_dict(mock_env_vars):
    """Test SignalClient initialization with a config dictionary overriding env vars."""
    config = {
        "phone_number": "+1111111111",
        "signal_service": "http://localhost:8080",
        "base_url": "http://localhost:8080",
        "worker_pool_size": 8,
    }
    client = SignalClient(config=config)
    settings = client.container.settings()
    assert settings.phone_number == "+1111111111"  # Overridden
    assert settings.signal_service == "http://localhost:8080"  # From env
    assert settings.worker_pool_size == 8  # Overridden
    asyncio.run(client.shutdown())


def test_signal_client_init_missing_required():
    """Test SignalClient raises ConfigurationError when settings are missing."""
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigurationError):
            SignalClient()


def test_signal_client_init_with_config_only():
    """SignalClient can initialize from config without environment variables."""

    with mock.patch.dict(os.environ, {}, clear=True):
        config = {
            "phone_number": "+2222222222",
            "signal_service": "ws://localhost:8081",
            "base_url": "http://localhost:8081",
            "worker_pool_size": 2,
        }
        client = SignalClient(config=config)
        settings = client.container.settings()

        assert settings.phone_number == "+2222222222"
        assert settings.signal_service == "ws://localhost:8081"
        assert settings.worker_pool_size == 2
        asyncio.run(client.shutdown())


def test_settings_invalid_redis_configuration():
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
    config = {"storage_type": "sqlite", "sqlite_database": ""}
    with pytest.raises(ConfigurationError, match="sqlite_database"):
        Settings.from_sources(config=config)


def test_settings_invalid_config_overrides_report_missing_fields(mock_env_vars):
    config = {"phone_number": None}
    with pytest.raises(ConfigurationError, match="phone_number"):
        Settings.from_sources(config=config)
