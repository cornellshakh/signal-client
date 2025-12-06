"""Messages API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient, RequestOptions


class MessagesClient(BaseClient):
    """Client for interacting with the Signal Messages API.

    Provides methods for sending messages, managing typing indicators, and
    (conceptually) retrieving messages, though message history is via websocket.
    """

    async def send(
        self,
        data: dict[str, Any],
        *,
        request_options: RequestOptions | None = None,
    ) -> dict[str, Any]:
        """Send a Signal message.

        Args:
            data: A dictionary containing the message payload.
            request_options: Optional request options for the API call.

        Returns:
            A dictionary confirming the message was sent.

        """
        response = await self._make_request(
            "POST", "/v2/send", json=data, request_options=request_options
        )
        return cast("dict[str, Any]", response)

    async def get_messages(
        self, phone_number: str, recipient: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Get messages from a recipient.

        Note: The Signal REST API does not expose a message history endpoint.
        Message persistence should be handled by using the websocket stream.

        Args:
            phone_number: The phone number of the account.
            recipient: The recipient of the messages.
            limit: Optional limit for the number of messages to retrieve.

        Raises:
            NotImplementedError: This method is not implemented as the REST API
                                 does not support message history retrieval.

        """
        msg = (
            "The REST API does not expose a message history endpoint. "
            "Use the websocket stream to persist messages instead."
        )
        raise NotImplementedError(msg)

    async def remote_delete(
        self,
        phone_number: str,
        data: dict[str, Any],
        *,
        request_options: RequestOptions | None = None,
    ) -> dict[str, Any]:
        """Remotely delete a Signal message.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing details for the message to delete.
            request_options: Optional request options for the API call.

        Returns:
            A dictionary confirming the message deletion.

        """
        response = await self._make_request(
            "DELETE",
            f"/v1/remote-delete/{phone_number}",
            json=data,
            request_options=request_options,
        )
        return cast("dict[str, Any]", response)

    async def set_typing_indicator(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set the typing indicator for a conversation.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing details for the typing indicator.

        Returns:
            A dictionary confirming the typing indicator was set.

        """
        response = await self._make_request(
            "PUT", f"/v1/typing-indicator/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def unset_typing_indicator(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Unset (hide) the typing indicator for a conversation.

        Args:
            phone_number: The phone number of the account.
            data: A dictionary containing details for the typing indicator.

        Returns:
            A dictionary confirming the typing indicator was unset.

        """
        response = await self._make_request(
            "DELETE", f"/v1/typing-indicator/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)
