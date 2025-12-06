"""Tests for the compatibility module."""

from __future__ import annotations

import importlib

import pytest

from signal_client import SignalClient
from signal_client.core.compatibility import (
    SUPPORTED_MATRIX,
    CompatibilityError,
    check_supported_versions,
)


@pytest.fixture(autouse=True)
def _reload_metadata(monkeypatch):
    """Reload metadata for compatibility tests."""
    original = importlib.import_module("importlib.metadata")

    versions: dict[str, str] = {}

    def fake_version(package: str) -> str:
        if package not in versions:
            raise original.PackageNotFoundError(package)
        return versions[package]

    monkeypatch.setattr(
        "signal_client.core.compatibility.metadata.version", fake_version
    )
    monkeypatch.setattr(
        "signal_client.core.compatibility.metadata.PackageNotFoundError",
        original.PackageNotFoundError,
    )

    for package, supported_range in SUPPORTED_MATRIX.items():
        versions[package] = str(supported_range.minimum_inclusive)

    return versions


def test_check_supported_versions_passes_within_ranges():
    """Test that check_supported_versions passes within valid ranges."""
    # Should not raise when all versions are at the lower bound
    check_supported_versions()


def test_check_supported_versions_raises_outside_range(_reload_metadata):
    """Test that check_supported_versions raises for versions outside the range."""
    versions = _reload_metadata
    package = next(iter(SUPPORTED_MATRIX))
    versions[package] = str(SUPPORTED_MATRIX[package].maximum_exclusive)

    with pytest.raises(CompatibilityError):
        check_supported_versions()


def test_signal_client_initialization_raises_on_incompatible_version(
    monkeypatch, _reload_metadata
):
    """Test that SignalClient initialization raises on incompatible versions."""
    versions = _reload_metadata
    versions["pydantic"] = "3.0.0"

    config = {
        "phone_number": "+1234567890",
        "signal_service": "localhost:8080",
        "base_url": "http://localhost:8080",
    }

    with pytest.raises(CompatibilityError):
        SignalClient(config=config)
