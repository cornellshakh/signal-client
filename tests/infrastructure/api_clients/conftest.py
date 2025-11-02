from __future__ import annotations

from collections.abc import AsyncGenerator

import aiohttp
import pytest_asyncio

from signal_client.infrastructure.api_clients import (
    AccountsClient,
    AttachmentsClient,
    ContactsClient,
    DevicesClient,
    GeneralClient,
    GroupsClient,
    IdentitiesClient,
    MessagesClient,
    ProfilesClient,
    ReactionsClient,
    ReceiptsClient,
    SearchClient,
    StickerPacksClient,
)


@pytest_asyncio.fixture
async def accounts_client() -> AsyncGenerator[AccountsClient, None]:
    """Fixture for an AccountsClient."""
    async with aiohttp.ClientSession() as session:
        yield AccountsClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def attachments_client() -> AsyncGenerator[AttachmentsClient, None]:
    """Fixture for an AttachmentsClient."""
    async with aiohttp.ClientSession() as session:
        yield AttachmentsClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def contacts_client() -> AsyncGenerator[ContactsClient, None]:
    """Fixture for a ContactsClient."""
    async with aiohttp.ClientSession() as session:
        yield ContactsClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def devices_client() -> AsyncGenerator[DevicesClient, None]:
    """Fixture for a DevicesClient."""
    async with aiohttp.ClientSession() as session:
        yield DevicesClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def general_client() -> AsyncGenerator[GeneralClient, None]:
    """Fixture for a GeneralClient."""
    async with aiohttp.ClientSession() as session:
        yield GeneralClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def groups_client() -> AsyncGenerator[GroupsClient, None]:
    """Fixture for a GroupsClient."""
    async with aiohttp.ClientSession() as session:
        yield GroupsClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def identities_client() -> AsyncGenerator[IdentitiesClient, None]:
    """Fixture for an IdentitiesClient."""
    async with aiohttp.ClientSession() as session:
        yield IdentitiesClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def messages_client() -> AsyncGenerator[MessagesClient, None]:
    """Fixture for a MessagesClient."""
    async with aiohttp.ClientSession() as session:
        yield MessagesClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def profiles_client() -> AsyncGenerator[ProfilesClient, None]:
    """Fixture for a ProfilesClient."""
    async with aiohttp.ClientSession() as session:
        yield ProfilesClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def reactions_client() -> AsyncGenerator[ReactionsClient, None]:
    """Fixture for a ReactionsClient."""
    async with aiohttp.ClientSession() as session:
        yield ReactionsClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def receipts_client() -> AsyncGenerator[ReceiptsClient, None]:
    """Fixture for a ReceiptsClient."""
    async with aiohttp.ClientSession() as session:
        yield ReceiptsClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def search_client() -> AsyncGenerator[SearchClient, None]:
    """Fixture for a SearchClient."""
    async with aiohttp.ClientSession() as session:
        yield SearchClient(session=session, base_url="http://localhost:8080")


@pytest_asyncio.fixture
async def sticker_packs_client() -> AsyncGenerator[StickerPacksClient, None]:
    """Fixture for a StickerPacksClient."""
    async with aiohttp.ClientSession() as session:
        yield StickerPacksClient(session=session, base_url="http://localhost:8080")
