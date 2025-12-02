from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from .infrastructure.schemas.message import Message
from .infrastructure.schemas.reactions import ReactionRequest
from .infrastructure.schemas.requests import (
    SendMessageRequest,
    TypingIndicatorRequest,
)

if TYPE_CHECKING:
    from .context_deps import ContextDependencies


class Context:
    def __init__(
        self,
        message: Message,
        dependencies: ContextDependencies,
    ) -> None:
        self.message = message
        self.accounts = dependencies.accounts_client
        self.attachments = dependencies.attachments_client
        self.contacts = dependencies.contacts_client
        self.devices = dependencies.devices_client
        self.general = dependencies.general_client
        self.groups = dependencies.groups_client
        self.identities = dependencies.identities_client
        self.messages = dependencies.messages_client
        self.profiles = dependencies.profiles_client
        self.reactions = dependencies.reactions_client
        self.receipts = dependencies.receipts_client
        self.search = dependencies.search_client
        self.sticker_packs = dependencies.sticker_packs_client
        self._phone_number = dependencies.phone_number
        self._lock_manager = dependencies.lock_manager

    async def send(self, request: SendMessageRequest) -> None:
        """Send a message to a recipient."""
        if not request.recipients:
            request.recipients = [self.message.recipient()]
        if request.number is None:
            request.number = self._phone_number
        await self.messages.send(request.model_dump(exclude_none=True))

    async def reply(self, request: SendMessageRequest) -> None:
        """Reply to the incoming message, quoting it."""
        request.quote_author = self.message.source
        request.quote_message = self.message.message
        request.quote_timestamp = self.message.timestamp
        await self.send(request)

    async def react(self, emoji: str) -> None:
        """Add a reaction to the incoming message."""
        request = ReactionRequest(
            emoji=emoji,
            target_author=self.message.source,
            target_timestamp=self.message.timestamp,
        )
        if self.message.is_group() and self.message.group:
            request.group = self.message.group["groupId"]
        else:
            request.recipient = self.message.source
        await self.reactions.send_reaction(
            self._phone_number, request.model_dump(exclude_none=True)
        )

    async def remove_reaction(self) -> None:
        """Remove a reaction from the incoming message."""
        if not self.message.reaction_emoji:
            return

        request = ReactionRequest(
            emoji=self.message.reaction_emoji,
            target_author=self.message.source,
            target_timestamp=self.message.timestamp,
        )
        if self.message.is_group() and self.message.group:
            request.group = self.message.group["groupId"]
        else:
            request.recipient = self.message.source
        await self.reactions.remove_reaction(
            self._phone_number, request.model_dump(exclude_none=True)
        )

    async def start_typing(self) -> None:
        """Show the typing indicator."""
        request = TypingIndicatorRequest()
        if self.message.is_group() and self.message.group:
            request.group = self.message.group["groupId"]
        else:
            request.recipient = self.message.source
        await self.messages.set_typing_indicator(
            self._phone_number, request.model_dump(exclude_none=True)
        )

    async def stop_typing(self) -> None:
        """Hide the typing indicator."""
        request = TypingIndicatorRequest()
        if self.message.is_group() and self.message.group:
            request.group = self.message.group["groupId"]
        else:
            request.recipient = self.message.source
        await self.messages.unset_typing_indicator(
            self._phone_number, request.model_dump(exclude_none=True)
        )

    @asynccontextmanager
    async def lock(self, resource_id: str) -> AsyncGenerator[None, None]:
        """Acquire a lock for a specific resource."""
        async with self._lock_manager.lock(resource_id):
            yield
