from __future__ import annotations

import pytest
from aresponses import ResponsesMock

from signal_client.infrastructure.api_clients.accounts_client import AccountsClient


@pytest.mark.asyncio
async def test_get_accounts(
    accounts_client: AccountsClient, aresponses: ResponsesMock
) -> None:
    aresponses.add(
        "localhost:8080",
        "/v1/accounts",
        "GET",
        aresponses.Response(
            status=200,
            text="[]",
            headers={"Content-Type": "application/json"},
        ),
    )
    result = await accounts_client.get_accounts()
    assert result == []


@pytest.mark.asyncio
async def test_set_pin(
    accounts_client: AccountsClient, aresponses: ResponsesMock
) -> None:
    phone_number = "+1234567890"
    pin_data = {"pin": "1234"}
    aresponses.add(
        "localhost:8080",
        f"/v1/accounts/{phone_number}/pin",
        "POST",
        aresponses.Response(status=204),
    )
    await accounts_client.set_pin(phone_number, pin_data)


@pytest.mark.asyncio
async def test_remove_pin(
    accounts_client: AccountsClient, aresponses: ResponsesMock
) -> None:
    phone_number = "+1234567890"
    aresponses.add(
        "localhost:8080",
        f"/v1/accounts/{phone_number}/pin",
        "DELETE",
        aresponses.Response(status=204),
    )
    await accounts_client.remove_pin(phone_number)


@pytest.mark.asyncio
async def test_lift_rate_limit(
    accounts_client: AccountsClient, aresponses: ResponsesMock
) -> None:
    phone_number = "+1234567890"
    captcha_data = {"captcha": "test"}
    aresponses.add(
        "localhost:8080",
        f"/v1/accounts/{phone_number}/rate-limit-challenge",
        "POST",
        aresponses.Response(status=204),
    )
    await accounts_client.lift_rate_limit(phone_number, captcha_data)


@pytest.mark.asyncio
async def test_update_settings(
    accounts_client: AccountsClient, aresponses: ResponsesMock
) -> None:
    phone_number = "+1234567890"
    settings_data = {"theme": "dark"}
    aresponses.add(
        "localhost:8080",
        f"/v1/accounts/{phone_number}/settings",
        "PUT",
        aresponses.Response(status=204),
    )
    await accounts_client.update_settings(phone_number, settings_data)


@pytest.mark.asyncio
async def test_set_username(
    accounts_client: AccountsClient, aresponses: ResponsesMock
) -> None:
    phone_number = "+1234567890"
    username_data = {"username": "test"}
    aresponses.add(
        "localhost:8080",
        f"/v1/accounts/{phone_number}/username",
        "POST",
        aresponses.Response(status=204),
    )
    await accounts_client.set_username(phone_number, username_data)


@pytest.mark.asyncio
async def test_remove_username(
    accounts_client: AccountsClient, aresponses: ResponsesMock
) -> None:
    phone_number = "+1234567890"
    aresponses.add(
        "localhost:8080",
        f"/v1/accounts/{phone_number}/username",
        "DELETE",
        aresponses.Response(status=204),
    )
    await accounts_client.remove_username(phone_number)
