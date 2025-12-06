"""Reactions API client wrappers."""

from __future__ import annotations

from typing import Any, cast

from .base_client import BaseClient


class ReactionsClient(BaseClient):
    """Client for interacting with the Signal Reactions API.

    Provides methods for sending and removing reactions to messages.
    """

    async def send_reaction(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a reaction to a message.

        Args:
            phone_number: The phone number of the account sending the reaction.
            data: A dictionary containing the reaction details.

        Returns:
            A dictionary confirming the reaction was sent.

        """
        response = await self._make_request(
            "POST", f"/v1/reactions/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)

    async def remove_reaction(
        self, phone_number: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Remove a reaction from a message.

        Args:
            phone_number: The phone number of the account removing the reaction.
            data: A dictionary containing the reaction details to remove.

        Returns:
            A dictionary confirming the reaction was removed.

        """
        response = await self._make_request(
            "DELETE", f"/v1/reactions/{phone_number}", json=data
        )
        return cast("dict[str, Any]", response)
