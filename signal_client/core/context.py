"""Context utilities exposed to command handlers."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from signal_client.adapters.api.request_options import RequestOptions
from signal_client.adapters.api.schemas.link_preview import LinkPreview
from signal_client.adapters.api.schemas.message import AttachmentPointer, Message
from signal_client.adapters.api.schemas.reactions import ReactionRequest
from signal_client.adapters.api.schemas.receipts import ReceiptRequest
from signal_client.adapters.api.schemas.requests import (
    MessageMention,
    RemoteDeleteRequest,
    SendMessageRequest,
    TypingIndicatorRequest,
)
from signal_client.adapters.api.schemas.responses import (
    RemoteDeleteResponse,
    SendMessageResponse,
)
from signal_client.runtime.services.attachment_downloader import AttachmentDownloader

if TYPE_CHECKING:
    from signal_client.core.context_deps import ContextDependencies


DEFAULT_MAX_TOTAL_BYTES = 25 * 1024 * 1024


class Context:
    """Provide helpers for command handlers interacting with the Signal API.

    Instances of this class are passed to command handler functions,
    encapsulating the incoming message and all necessary API clients
    and utilities.
    """

    def __init__(
        self,
        message: Message,
        dependencies: ContextDependencies,
    ) -> None:
        """Initialize a Context instance.

        Args:
            message: The incoming message that triggered the command.
            dependencies: An instance of ContextDependencies providing
                          access to various clients and managers.

        """
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

        self._attachment_downloader = AttachmentDownloader(self.attachments)

    async def send(self, request: SendMessageRequest) -> SendMessageResponse | None:
        """Send a message to a recipient.

        Args:
            request: The SendMessageRequest object containing message details.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
        normalized = self._prepare_send_request(request)
        request_options = (
            RequestOptions(idempotency_key=normalized.idempotency_key)
            if normalized.idempotency_key
            else None
        )
        response = await self.messages.send(
            normalized.model_dump(exclude_none=True, by_alias=True),
            request_options=request_options,
        )
        return SendMessageResponse.from_raw(response)

    async def reply(self, request: SendMessageRequest) -> SendMessageResponse | None:
        """Reply to the incoming message, quoting it.

        The original message's author, content, and timestamp are
        automatically included in the quote.

        Args:
            request: The SendMessageRequest object containing message details.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
        request.quote_author = self.message.source
        request.quote_message = self.message.message
        request.quote_timestamp = self.message.timestamp
        return await self.send(request)

    async def send_text(  # noqa: PLR0913
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
        """Send a plain text message.

        Args:
            text: The text content of the message.
            recipients: Optional list of recipient IDs (phone numbers or group
                IDs). Defaults to the sender of the incoming message.
            mentions: Optional list of MessageMention objects for @mentions.
            quote_mentions: Optional list of MessageMention objects for mentions
                within a quote.
            base64_attachments: Optional list of base64 encoded attachments.
            link_preview: Optional LinkPreview object for a URL preview.
            text_mode: 'normal' for plain text, 'styled' for markdown.
            notify_self: Whether to send a notification to self.
            edit_timestamp: Timestamp of the message to edit.
            sticker: ID of a sticker to send.
            view_once: If True, the message/attachments can only be viewed once.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
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

    async def reply_text(  # noqa: PLR0913
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
        """Reply to the incoming message with plain text, quoting it.

        Args:
            text: The text content of the reply message.
            recipients: Optional list of recipient IDs (phone numbers or group
                IDs). Defaults to the sender of the incoming message.
            mentions: Optional list of MessageMention objects for @mentions.
            quote_mentions: Optional list of MessageMention objects for mentions
                within a quote.
            base64_attachments: Optional list of base64 encoded attachments.
            link_preview: Optional LinkPreview object for a URL preview.
            text_mode: 'normal' for plain text, 'styled' for markdown.
            notify_self: Whether to send a notification to self.
            edit_timestamp: Timestamp of the message to edit.
            sticker: ID of a sticker to send.
            view_once: If True, the message/attachments can only be viewed once.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
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
        """Send a message with markdown formatting.

        Args:
            text: The markdown formatted text content of the message.
            recipients: Optional list of recipient IDs.
            mentions: Optional list of MessageMention objects for @mentions.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
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
        """Send a sticker message.

        Args:
            pack_id: The ID of the sticker pack.
            sticker_id: The ID of the sticker within the pack.
            caption: Optional caption for the sticker.
            recipients: Optional list of recipient IDs.
            notify_self: Whether to send a notification to self.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
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
        """Send a view-once message with attachments.

        Args:
            attachments: List of base64 encoded attachments.
            message: Optional text message to accompany the view-once attachments.
            recipients: Optional list of recipient IDs.
            notify_self: Whether to send a notification to self.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
        return await self.send_text(
            message,
            recipients=recipients,
            base64_attachments=attachments,
            view_once=True,
            notify_self=notify_self,
        )

    async def send_with_preview(  # noqa: PLR0913
        self,
        url: str,
        *,
        message: str | None = None,
        title: str | None = None,
        description: str | None = None,
        recipients: Sequence[str] | None = None,
        text_mode: Literal["normal", "styled"] | None = None,
    ) -> SendMessageResponse | None:
        """Send a message with a link preview.

        Args:
            url: The URL for which to generate a preview.
            message: Optional text message to accompany the link preview.
            title: Optional title for the link preview.
            description: Optional description for the link preview.
            recipients: Optional list of recipient IDs.
            text_mode: 'normal' for plain text, 'styled' for markdown.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
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

    @asynccontextmanager
    async def download_attachments(
        self,
        attachments: Sequence[AttachmentPointer] | None = None,
        *,
        max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
        dest_dir: str | Path | None = None,
    ) -> AsyncGenerator[list[Path], None]:
        """Download attachments associated with the current message or a provided list.

        This is an asynchronous context manager that yields a list of `Path`
        objects pointing to the downloaded files. The files are cleaned up
        automatically upon exiting the context.

        Args:
            attachments: An optional sequence of `AttachmentPointer` objects
                to download.
                If not provided, attachments from `self.message` are used.
            max_total_bytes: The maximum total size (in bytes) of attachments
                to download.
                Defaults to `DEFAULT_MAX_TOTAL_BYTES`.
            dest_dir: Optional directory to save the attachments. If not
                provided, a temporary directory is used.

        Yields:
            A list of `pathlib.Path` objects to the downloaded attachment files.

        """
        pointers: list[AttachmentPointer] = []
        if attachments is not None:
            pointers = list(attachments)
        elif self.message.attachments:
            pointers = list(self.message.attachments)

        downloader = (
            self._attachment_downloader
            if max_total_bytes == self._attachment_downloader.max_total_bytes
            else AttachmentDownloader(self.attachments, max_total_bytes=max_total_bytes)
        )
        async with downloader.download(pointers, dest_dir=dest_dir) as files:
            yield files

    def mention_author(
        self, text: str, mention_text: str | None = None
    ) -> MessageMention:
        """Create a MessageMention object for the author of the current message.

        Args:
            text: The full text content where the mention is located.
            mention_text: The specific text used for the mention (e.g., "@Alice").
                          If None, defaults to `self.message.source`.

        Returns:
            A `MessageMention` object suitable for use in `SendMessageRequest`.

        Raises:
            ValueError: If the `mention_text` is not found within the provided `text`.

        """
        mention_value = mention_text or self.message.source
        start = text.find(mention_value)
        if start < 0:
            message = "mention text must exist within the provided text"
            raise ValueError(message)
        return MessageMention(
            author=self.message.source, start=start, length=len(mention_value)
        )

    async def reply_with_quote_mentions(
        self,
        text: str,
        mentions: list[MessageMention] | None = None,
    ) -> SendMessageResponse | None:
        """Reply with text while quoting and mentioning the original author.

        Attempts to mention the author of the original message when possible.

        Args:
            text: The text content of the reply message.
            mentions: Optional list of additional MessageMention objects for @mentions.

        Returns:
            A SendMessageResponse object if successful, otherwise None.

        """
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
        """Add a reaction (emoji) to the incoming message.

        Args:
            emoji: The emoji string to react with (e.g., "👍").

        """
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
        """Remove a reaction from the incoming message.

        This method will only attempt removal if `self.message.reaction_emoji` is
        set, indicating a reaction was present on the original message.
        """
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
        """Send a typing indicator to the sender of the incoming message."""
        request = TypingIndicatorRequest(recipient=self._recipient())
        await self.messages.set_typing_indicator(
            self._phone_number, request.model_dump(exclude_none=True, by_alias=True)
        )

    async def hide_typing(self) -> None:
        """Hide the typing indicator from the sender of the incoming message."""
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
        """Send a read or viewed receipt for a message.

        Args:
            target_timestamp: The timestamp of the message for which to send
                the receipt.
            receipt_type: The type of receipt to send ('read' or 'viewed').
                Defaults to 'read'.
            recipient: Optional recipient ID. Defaults to the sender of the
                incoming message.

        """
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
        idempotency_key: str | None = None,
    ) -> RemoteDeleteResponse | None:
        """Remotely delete a message.

        Args:
            target_timestamp: The timestamp of the message to delete.
            recipient: Optional recipient ID. Defaults to the sender of the
                incoming message.
            idempotency_key: An optional idempotency key for the request.

        Returns:
            A RemoteDeleteResponse object if successful, otherwise None.

        """
        request = RemoteDeleteRequest(
            recipient=recipient or self._recipient(),
            timestamp=target_timestamp,
            idempotency_key=idempotency_key,
        )
        request_options = (
            RequestOptions(idempotency_key=request.idempotency_key)
            if request.idempotency_key
            else None
        )
        response = await self.messages.remote_delete(
            self._phone_number,
            request.model_dump(exclude_none=True, by_alias=True),
            request_options=request_options,
        )
        return RemoteDeleteResponse.from_raw(response)

    @asynccontextmanager
    async def lock(self, resource_id: str) -> AsyncGenerator[None, None]:
        """Acquire a distributed lock for a specific resource.

        This is an asynchronous context manager that ensures exclusive access
        to a resource across multiple instances of the application.

        Args:
            resource_id: A unique identifier for the resource to lock.

        Yields:
            None, while the lock is held.

        """
        async with self._lock_manager.lock(resource_id):
            yield

    def _prepare_send_request(self, request: SendMessageRequest) -> SendMessageRequest:
        """Prepare a SendMessageRequest by backfilling recipient and sender number.

        Args:
            request: The SendMessageRequest to prepare.

        Returns:
            The prepared SendMessageRequest.

        """
        if not request.recipients:
            request.recipients = [self._recipient()]
        if request.number is None:
            request.number = self._phone_number
        return request

    def _recipient(self) -> str:
        """Determine the default recipient for a message based on the incoming message.

        If the incoming message is from a group, the group ID is returned.
        Otherwise, the sender's source ID is returned.

        Returns:
            The recipient ID (phone number or group ID).

        """
        if self.message.is_group() and self.message.group:
            return self.message.group["groupId"]
        return self.message.source
