from __future__ import annotations

import aiohttp

from .api_clients.accounts_client import AccountsClient
from .api_clients.attachments_client import AttachmentsClient
from .api_clients.contacts_client import ContactsClient
from .api_clients.devices_client import DevicesClient
from .api_clients.general_client import GeneralClient
from .api_clients.groups_client import GroupsClient
from .api_clients.identities_client import IdentitiesClient
from .api_clients.messages_client import MessagesClient
from .api_clients.profiles_client import ProfilesClient
from .api_clients.reactions_client import ReactionsClient
from .api_clients.receipts_client import ReceiptsClient
from .api_clients.search_client import SearchClient
from .api_clients.sticker_packs_client import StickerPacksClient


class APIService:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        signal_service: str,
        phone_number: str,
    ) -> None:
        self._session = session
        self._signal_service = signal_service
        self._phone_number = phone_number
        self._base_url = f"http://{self._signal_service}"

        self.accounts = AccountsClient(self._session, self._base_url)
        self.attachments = AttachmentsClient(self._session, self._base_url)
        self.contacts = ContactsClient(self._session, self._base_url)
        self.devices = DevicesClient(self._session, self._base_url)
        self.general = GeneralClient(self._session, self._base_url)
        self.groups = GroupsClient(self._session, self._base_url)
        self.identities = IdentitiesClient(self._session, self._base_url)
        self.messages = MessagesClient(self._session, self._base_url)
        self.profiles = ProfilesClient(self._session, self._base_url)
        self.reactions = ReactionsClient(self._session, self._base_url)
        self.receipts = ReceiptsClient(self._session, self._base_url)
        self.search = SearchClient(self._session, self._base_url)
        self.sticker_packs = StickerPacksClient(self._session, self._base_url)

    async def close(self) -> None:
        await self._session.close()
