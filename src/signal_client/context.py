from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Literal

from .infrastructure.schemas.link_preview import LinkPreview
from .infrastructure.schemas.message import Message
from .infrastructure.schemas.reactions import ReactionRequest
from .infrastructure.schemas.receipts import ReceiptRequest
from .infrastructure.schemas.requests import (
    MessageMention,
    RemoteDeleteRequest,
    SendMessageRequest,
    TypingIndicatorRequest,
)
from .infrastructure.schemas.responses import (
    RemoteDeleteResponse,
    SendMessageResponse,
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
        self.settings = dependencies.settings
        self._phone_number = dependencies.phone_number
        self._lock_manager = dependencies.lock_manager

    async def send(self, request: SendMessageRequest) -> SendMessageResponse | None:
        """Send a message to a recipient."""
        normalized = self._prepare_send_request(request)
        response = await self.messages.send(
            normalized.model_dump(exclude_none=True, by_alias=True)
        )
        return SendMessageResponse.from_raw(response)

    async def reply(self, request: SendMessageRequest) -> SendMessageResponse | None:
        """Reply to the incoming message, quoting it."""
        request.quote_author = self.message.source
        request.quote_message = self.message.message
        request.quote_timestamp = self.message.timestamp
        return await self.send(request)

    async def send_text(
        self,
        text: str,
        *,
        recipients: Sequence[str] | None = None,
        mentions: list[MessageMention] | None = None,
        quote_mentions: list[MessageMention] | None = None,
        base64_attachments: list[str] | None = None,
        link_preview: LinkPreview | None = None,
        text_mode: Literal["normal", "styled"] | None = None,
        notify_self: bool | None = None,
        edit_timestamp: int | None = None,
        sticker: str | None = None,
        view_once: bool = False,
    ) -> SendMessageResponse | None:
        request = SendMessageRequest(
            message=text,
            recipients=list(recipients) if recipients else None,
            base64_attachments=base64_attachments or [],
            mentions=mentions,
            quote_mentions=quote_mentions,
            link_preview=link_preview,
            text_mode=text_mode,
            notify_self=notify_self,
            edit_timestamp=edit_timestamp,
            sticker=sticker,
            view_once=view_once,
        )
        return await self.send(request)

    async def reply_text(
        self,
        text: str,
        *,
        recipients: Sequence[str] | None = None,
        mentions: list[MessageMention] | None = None,
        quote_mentions: list[MessageMention] | None = None,
        base64_attachments: list[str] | None = None,
        link_preview: LinkPreview | None = None,
        text_mode: Literal["normal", "styled"] | None = None,
        notify_self: bool | None = None,
        edit_timestamp: int | None = None,
        sticker: str | None = None,
        view_once: bool = False,
    ) -> SendMessageResponse | None:
        request = SendMessageRequest(
            message=text,
            recipients=list(recipients) if recipients else None,
            base64_attachments=base64_attachments or [],
            mentions=mentions,
            quote_mentions=quote_mentions,
            link_preview=link_preview,
            text_mode=text_mode,
            notify_self=notify_self,
            edit_timestamp=edit_timestamp,
            sticker=sticker,
            view_once=view_once,
        )
        return await self.reply(request)

    async def send_markdown(
        self,
        text: str,
        *,
        recipients: Sequence[str] | None = None,
        mentions: list[MessageMention] | None = None,
    ) -> SendMessageResponse | None:
        return await self.send_text(
            text,
            recipients=recipients,
            mentions=mentions,
            text_mode="styled",
        )

    async def send_sticker(
        self,
        pack_id: str,
        sticker_id: int | str,
        *,
        caption: str | None = None,
        recipients: Sequence[str] | None = None,
        notify_self: bool | None = None,
    ) -> SendMessageResponse | None:
        sticker_ref = f"{pack_id}:{sticker_id}"
        return await self.send_text(
            caption or "",
            recipients=recipients,
            sticker=sticker_ref,
            notify_self=notify_self,
        )

    async def send_view_once(
        self,
        attachments: list[str],
        *,
        message: str = "",
        recipients: Sequence[str] | None = None,
        notify_self: bool | None = None,
    ) -> SendMessageResponse | None:
        return await self.send_text(
            message,
            recipients=recipients,
            base64_attachments=attachments,
            view_once=True,
            notify_self=notify_self,
        )

    async def send_with_preview(
        self,
        url: str,
        *,
        message: str | None = None,
        title: str | None = None,
        description: str | None = None,
        recipients: Sequence[str] | None = None,
        text_mode: Literal["normal", "styled"] | None = None,
    ) -> SendMessageResponse | None:
        preview = LinkPreview(
            url=url,
            title=title,
            description=description,
        )
        return await self.send_text(
            message or url,
            recipients=recipients,
            link_preview=preview,
            text_mode=text_mode,
        )

    def mention_author(self, text: str, mention_text: str | None = None) -> MessageMention:
        mention_value = mention_text or self.message.source
        start = text.find(mention_value)
        if start < 0:
            message = "mention text must exist within the provided text"
            raise ValueError(message)
        return MessageMention(author=self.message.source, start=start, length=len(mention_value))

    async def reply_with_quote_mentions(
        self,
        text: str,
        mentions: list[MessageMention] | None = None,
    ) -> SendMessageResponse | None:
        quote_mentions = mentions
        if quote_mentions is None and self.message.message:
            try:
                quote_mentions = [self.mention_author(self.message.message)]
            except ValueError:
                quote_mentions = None

        return await self.reply_text(
            text,
            quote_mentions=quote_mentions,
        )

    async def react(self, emoji: str) -> None:
        """Add a reaction to the incoming message."""
        request = ReactionRequest(
            reaction=emoji,
            target_author=self.message.source,
            timestamp=self.message.timestamp,
            recipient=self._recipient(),
        )
        await self.reactions.send_reaction(
            self._phone_number,
            request.model_dump(by_alias=True, exclude_none=True),
        )

    async def remove_reaction(self) -> None:
        """Remove a reaction from the incoming message."""
        if not self.message.reaction_emoji:
            return

        request = ReactionRequest(
            reaction=self.message.reaction_emoji,
            target_author=self.message.source,
            timestamp=self.message.timestamp,
            recipient=self._recipient(),
        )
        await self.reactions.remove_reaction(
            self._phone_number,
            request.model_dump(by_alias=True, exclude_none=True),
        )

    async def show_typing(self) -> None:
        """Show the typing indicator."""
        request = TypingIndicatorRequest(recipient=self._recipient())
        await self.messages.set_typing_indicator(
            self._phone_number, request.model_dump(exclude_none=True, by_alias=True)
        )

    async def hide_typing(self) -> None:
        """Hide the typing indicator."""
        request = TypingIndicatorRequest(recipient=self._recipient())
        await self.messages.unset_typing_indicator(
            self._phone_number, request.model_dump(exclude_none=True, by_alias=True)
        )

    async def start_typing(self) -> None:
        """Alias for show_typing for backward compatibility."""
        await self.show_typing()

    async def stop_typing(self) -> None:
        """Alias for hide_typing for backward compatibility."""
        await self.hide_typing()

    async def send_receipt(
        self,
        target_timestamp: int,
        *,
        receipt_type: Literal["read", "viewed"] = "read",
        recipient: str | None = None,
    ) -> None:
        payload = ReceiptRequest(
            recipient=recipient or self._recipient(),
            timestamp=target_timestamp,
            receipt_type=receipt_type,
        )
        await self.receipts.send_receipt(
            self._phone_number,
            payload.model_dump(exclude_none=True, by_alias=True),
        )

    async def remote_delete(
        self,
        target_timestamp: int,
        *,
        recipient: str | None = None,
    ) -> RemoteDeleteResponse | None:
        request = RemoteDeleteRequest(
            recipient=recipient or self._recipient(),
            timestamp=target_timestamp,
        )
        response = await self.messages.remote_delete(
            self._phone_number,
            request.model_dump(exclude_none=True, by_alias=True),
        )
        return RemoteDeleteResponse.from_raw(response)

    @asynccontextmanager
    async def lock(self, resource_id: str) -> AsyncGenerator[None, None]:
        """Acquire a lock for a specific resource."""
        async with self._lock_manager.lock(resource_id):
            yield

    def _prepare_send_request(self, request: SendMessageRequest) -> SendMessageRequest:
        """Backfill recipients/number so callers never have to."""
        if not request.recipients:
            request.recipients = [self._recipient()]
        if request.number is None:
            request.number = self._phone_number
        return request

    def _recipient(self) -> str:
        if self.message.is_group() and self.message.group:
            return self.message.group["groupId"]
        return self.message.source
