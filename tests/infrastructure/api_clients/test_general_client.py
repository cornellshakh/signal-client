from __future__ import annotations

import pytest

from signal_client.infrastructure.api_clients.general_client import GeneralClient


@pytest.mark.asyncio
async def test_general_client(
    general_client: GeneralClient, aresponses
):
    """Test the general client."""
    # Arrange
    aresponses.add(
        "localhost:8080",
        "/v1/about",
        "GET",
        aresponses.Response(
            status=200,
            text='{"version": "0.1.0"}',
            headers={"Content-Type": "application/json"},
        ),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/configuration",
        "GET",
        aresponses.Response(
            status=200,
            text='{"key": "value"}',
            headers={"Content-Type": "application/json"},
        ),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/configuration",
        "POST",
        aresponses.Response(status=204),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/configuration/phonenumber/settings",
        "GET",
        aresponses.Response(
            status=200,
            text='{"key": "value"}',
            headers={"Content-Type": "application/json"},
        ),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/configuration/phonenumber/settings",
        "POST",
        aresponses.Response(status=204),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/health",
        "GET",
        aresponses.Response(
            status=200,
            text='{"status": "ok"}',
            headers={"Content-Type": "application/json"},
        ),
    )

    # Act
    about = await general_client.get_about()
    config = await general_client.get_configuration()
    await general_client.set_configuration({})
    settings = await general_client.get_settings("phonenumber")
    await general_client.set_settings("phonenumber", {})
    health = await general_client.get_health()

    # Assert
    assert about == {"version": "0.1.0"}
    assert config == {"key": "value"}
    assert settings == {"key": "value"}
    assert health == {"status": "ok"}