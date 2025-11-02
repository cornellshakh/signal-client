from __future__ import annotations

import pytest

from signal_client.infrastructure.api_clients.devices_client import DevicesClient


@pytest.mark.asyncio
async def test_devices_client(
    devices_client: DevicesClient, aresponses
):
    """Test the devices client."""
    # Arrange
    aresponses.add(
        "localhost:8080",
        "/v1/devices/phonenumber",
        "GET",
        aresponses.Response(
            status=200,
            text='[{"id": "device1"}]',
            headers={"Content-Type": "application/json"},
        ),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/devices/phonenumber",
        "POST",
        aresponses.Response(status=204),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/qrcodelink",
        "GET",
        aresponses.Response(
            status=200,
            text='{"url": "some-url"}',
            headers={"Content-Type": "application/json"},
        ),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/register/phonenumber",
        "POST",
        aresponses.Response(status=204),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/register/phonenumber/verify/token",
        "POST",
        aresponses.Response(status=204),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/unregister/phonenumber",
        "POST",
        aresponses.Response(status=204),
    )

    # Act
    devices = await devices_client.get_devices("phonenumber")
    await devices_client.add_device("phonenumber", {})
    qrcode = await devices_client.get_qrcodelink()
    await devices_client.register("phonenumber")
    await devices_client.verify("phonenumber", "token")
    await devices_client.unregister("phonenumber")

    # Assert
    assert devices == [{"id": "device1"}]
    assert qrcode == {"url": "some-url"}