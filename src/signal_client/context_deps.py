from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Settings
    from .infrastructure.api_clients import (
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
    from .services.lock_manager import LockManager


@dataclass
class ContextDependencies:
    """
    Holds all the external dependencies required by the `Context` object.
    """
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
