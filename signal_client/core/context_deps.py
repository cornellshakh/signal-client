"""Typed bundle of dependencies injected into Context instances."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signal_client.adapters.api import (
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
    from signal_client.core.config import Settings
    from signal_client.runtime.services.lock_manager import LockManager


@dataclass
class ContextDependencies:
    """Holds all the external dependencies required by the `Context` object."""

    accounts_client: AccountsClient
    attachments_client: AttachmentsClient
    contacts_client: ContactsClient
    devices_client: DevicesClient
    general_client: GeneralClient
    groups_client: GroupsClient
    identities_client: IdentitiesClient
    messages_client: MessagesClient
    profiles_client: ProfilesClient
    reactions_client: ReactionsClient
    receipts_client: ReceiptsClient
    search_client: SearchClient
    sticker_packs_client: StickerPacksClient
    lock_manager: LockManager
    phone_number: str
    settings: Settings
