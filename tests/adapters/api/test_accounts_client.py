"""Tests for the AccountsClient."""

from __future__ import annotations

from re import Pattern
from typing import Any, cast

import pytest
from aresponses.main import ResponsesMockServer

from signal_client.adapters.api.accounts_client import AccountsClient


@pytest.mark.asyncio
async def test_get_accounts(
    accounts_client: AccountsClient, aresponses: ResponsesMockServer
) -> None:
    """Test retrieving accounts."""
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", "/v1/accounts"),
        cast("Pattern[str]", "GET"),
        cast(
            "Any",
            aresponses.Response(
                status=200,
                text="[]",
                headers={"Content-Type": "application/json"},
            ),
        ),
    )
    result = await accounts_client.get_accounts()
    assert result == []


@pytest.mark.asyncio
async def test_set_pin(
    accounts_client: AccountsClient, aresponses: ResponsesMockServer
) -> None:
    """Test setting an account PIN."""
    phone_number = "+1234567890"
    pin_data = {"pin": "1234"}
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/accounts/{phone_number}/pin"),
        cast("Pattern[str]", "POST"),
        cast("Any", aresponses.Response(status=204)),
    )
    await accounts_client.set_pin(phone_number, pin_data)


@pytest.mark.asyncio
async def test_remove_pin(
    accounts_client: AccountsClient, aresponses: ResponsesMockServer
) -> None:
    """Test removing an account PIN."""
    phone_number = "+1234567890"
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/accounts/{phone_number}/pin"),
        cast("Pattern[str]", "DELETE"),
        cast("Any", aresponses.Response(status=204)),
    )
    await accounts_client.remove_pin(phone_number)


@pytest.mark.asyncio
async def test_lift_rate_limit(
    accounts_client: AccountsClient, aresponses: ResponsesMockServer
) -> None:
    """Test lifting a rate limit."""
    phone_number = "+1234567890"
    captcha_data = {"captcha": "test"}
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/accounts/{phone_number}/rate-limit-challenge"),
        cast("Pattern[str]", "POST"),
        cast("Any", aresponses.Response(status=204)),
    )
    await accounts_client.lift_rate_limit(phone_number, captcha_data)


@pytest.mark.asyncio
async def test_update_settings(
    accounts_client: AccountsClient, aresponses: ResponsesMockServer
) -> None:
    """Test updating account settings."""
    phone_number = "+1234567890"
    settings_data = {"theme": "dark"}
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/accounts/{phone_number}/settings"),
        cast("Pattern[str]", "PUT"),
        cast("Any", aresponses.Response(status=204)),
    )
    await accounts_client.update_settings(phone_number, settings_data)


@pytest.mark.asyncio
async def test_set_username(
    accounts_client: AccountsClient, aresponses: ResponsesMockServer
) -> None:
    """Test setting an account username."""
    phone_number = "+1234567890"
    username_data = {"username": "test"}
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/accounts/{phone_number}/username"),
        cast("Pattern[str]", "POST"),
        cast("Any", aresponses.Response(status=204)),
    )
    await accounts_client.set_username(phone_number, username_data)


@pytest.mark.asyncio
async def test_remove_username(
    accounts_client: AccountsClient, aresponses: ResponsesMockServer
) -> None:
    """Test removing an account username."""
    phone_number = "+1234567890"
    aresponses.add(
        cast("Pattern[str]", "localhost:8080"),
        cast("Pattern[str]", f"/v1/accounts/{phone_number}/username"),
        cast("Pattern[str]", "DELETE"),
        cast("Any", aresponses.Response(status=204)),
    )
    await accounts_client.remove_username(phone_number)
