from __future__ import annotations

from .domain.message import Message
from .infrastructure.api_models import (
    ReactionRequest,
    SendMessageRequest,
    TypingIndicatorRequest,
)
from .infrastructure.api_service import APIService


class Context:
    def __init__(
        self, message: Message, api_service: APIService, phone_number: str
    ) -> None:
        self.message = message
        self._api_service = api_service
        self._phone_number = phone_number

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
        await self._api_service.messages.send(request.model_dump(exclude_none=True))

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
        await self._api_service.messages.send(request.model_dump(exclude_none=True))

    async def react(self, emoji: str) -> None:
        """Add a reaction to the incoming message."""
        request = ReactionRequest(
            emoji=emoji,
            target_author=self.message.source,
            target_timestamp=self.message.timestamp,
        )
        if self.message.is_group():
            request.group = self.message.group
        else:
            request.recipient = self.message.source
        await self._api_service.reactions.send_reaction(
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
        if self.message.is_group():
            request.group = self.message.group
        else:
            request.recipient = self.message.source
        await self._api_service.reactions.remove_reaction(
            self._phone_number, request.model_dump(exclude_none=True)
        )

    async def start_typing(self) -> None:
        """Show the typing indicator."""
        request = TypingIndicatorRequest()
        if self.message.is_group():
            request.group = self.message.group
        else:
            request.recipient = self.message.source
        await self._api_service.messages.set_typing_indicator(
            self._phone_number, request.model_dump(exclude_none=True)
        )

    async def stop_typing(self) -> None:
        """Hide the typing indicator."""
        request = TypingIndicatorRequest()
        if self.message.is_group():
            request.group = self.message.group
        else:
            request.recipient = self.message.source
        await self._api_service.messages.unset_typing_indicator(
            self._phone_number, request.model_dump(exclude_none=True)
        )
