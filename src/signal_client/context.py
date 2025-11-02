from __future__ import annotations

from typing import TYPE_CHECKING

from .infrastructure.schemas.message import Message
from .infrastructure.schemas.reactions import ReactionRequest
from .infrastructure.schemas.requests import (
    SendMessageRequest,
    TypingIndicatorRequest,
)

if TYPE_CHECKING:
    from .container import Container


class Context:
    def __init__(self, container: Container, message: Message) -> None:
        self.message = message
        self.accounts = container.accounts_client()
        self.attachments = container.attachments_client()
        self.contacts = container.contacts_client()
        self.devices = container.devices_client()
        self.general = container.general_client()
        self.groups = container.groups_client()
        self.identities = container.identities_client()
        self.lock_manager = container.lock_manager()
        self.messages = container.messages_client()
        self.profiles = container.profiles_client()
        self.reactions = container.reactions_client()
        self.receipts = container.receipts_client()
        self.search = container.search_client()
        self.sticker_packs = container.sticker_packs_client()
        self._phone_number = container.config.phone_number()

    async def send(
        self,
        text: str,
        recipients: list[str] | None = None,
        base64_attachments: list[str] | None = None,
        mentions: list[dict] | None = None,
        *,
        view_once: bool = False,
    ) -> None:
        """Send a message to a recipient."""
        if recipients is None:
            recipients = [self.message.recipient()]

        request = SendMessageRequest(
            message=text,
            recipients=recipients,
            number=self._phone_number,
            base64_attachments=base64_attachments or [],
            mentions=mentions,
            view_once=view_once,
        )
        await self.messages.send(request.model_dump(exclude_none=True))

    async def reply(
        self,
        text: str,
        base64_attachments: list[str] | None = None,
        mentions: list[dict] | None = None,
        *,
        view_once: bool = False,
    ) -> None:
        """Reply to the incoming message, quoting it."""
        request = SendMessageRequest(
            message=text,
            recipients=[self.message.recipient()],
            number=self._phone_number,
            quote_author=self.message.source,
            quote_message=self.message.message,
            quote_timestamp=self.message.timestamp,
            base64_attachments=base64_attachments or [],
            mentions=mentions,
            view_once=view_once,
        )
        await self.messages.send(request.model_dump(exclude_none=True))

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
