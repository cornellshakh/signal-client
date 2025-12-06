"""Groups API client wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from .base_client import BaseClient

if TYPE_CHECKING:
    from .schemas.groups import (
        ChangeGroupAdminsRequest,
        ChangeGroupMembersRequest,
        CreateGroupRequest,
        UpdateGroupRequest,
    )


class GroupsClient(BaseClient):
    """Client for interacting with the Signal Groups API.

    Provides methods for managing groups, including creating, retrieving,
    updating, deleting, and managing members and admins.
    """

    async def get_groups(self, phone_number: str) -> list[dict[str, Any]]:
        """Retrieve a list of all Signal Groups associated with a phone number.

        Args:
            phone_number: The phone number of the account.

        Returns:
            A list of dictionaries, each representing a Signal Group.

        """
        response = await self._make_request("GET", f"/v1/groups/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def create_group(
        self, phone_number: str, request: CreateGroupRequest
    ) -> dict[str, Any]:
        """Create a new Signal Group.

        Args:
            phone_number: The phone number of the account creating the group.
            request: An object containing the details for creating the group.

        Returns:
            A dictionary containing information about the newly created group.

        """
        response = await self._make_request(
            "POST", f"/v1/groups/{phone_number}", json=request.model_dump()
        )
        return cast("dict[str, Any]", response)

    async def get_group(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Retrieve details of a specific Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to retrieve.

        Returns:
            A dictionary containing the details of the specified group.

        """
        response = await self._make_request(
            "GET", f"/v1/groups/{phone_number}/{group_id}"
        )
        return cast("dict[str, Any]", response)

    async def update_group(
        self, phone_number: str, group_id: str, request: UpdateGroupRequest
    ) -> dict[str, Any]:
        """Update the state of a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to update.
            request: An object containing the updated group details.

        Returns:
            A dictionary confirming the group update.

        """
        response = await self._make_request(
            "PUT",
            f"/v1/groups/{phone_number}/{group_id}",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def delete_group(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Delete a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to delete.

        Returns:
            A dictionary confirming the group deletion.

        """
        response = await self._make_request(
            "DELETE", f"/v1/groups/{phone_number}/{group_id}"
        )
        return cast("dict[str, Any]", response)

    async def add_admins(
        self, phone_number: str, group_id: str, request: ChangeGroupAdminsRequest
    ) -> dict[str, Any]:
        """Add administrators to a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to modify.
            request: An object specifying the admins to add.

        Returns:
            A dictionary confirming the admin addition.

        """
        response = await self._make_request(
            "POST",
            f"/v1/groups/{phone_number}/{group_id}/admins",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def remove_admins(
        self, phone_number: str, group_id: str, request: ChangeGroupAdminsRequest
    ) -> dict[str, Any]:
        """Remove administrators from a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to modify.
            request: An object specifying the admins to remove.

        Returns:
            A dictionary confirming the admin removal.

        """
        response = await self._make_request(
            "DELETE",
            f"/v1/groups/{phone_number}/{group_id}/admins",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def get_avatar(self, phone_number: str, group_id: str) -> bytes:
        """Retrieve the avatar of a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group.

        Returns:
            The avatar image as bytes.

        """
        response = await self._make_request(
            "GET", f"/v1/groups/{phone_number}/{group_id}/avatar"
        )
        return cast("bytes", response)

    async def set_avatar(
        self, phone_number: str, group_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Set the avatar of a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group.
            data: A dictionary containing the new avatar data.

        Returns:
            A dictionary confirming the avatar update.

        """
        response = await self._make_request(
            "PUT", f"/v1/groups/{phone_number}/{group_id}/avatar", json=data
        )
        return cast("dict[str, Any]", response)

    async def block(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Block a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to block.

        Returns:
            A dictionary confirming the group block.

        """
        response = await self._make_request(
            "POST", f"/v1/groups/{phone_number}/{group_id}/block"
        )
        return cast("dict[str, Any]", response)

    async def unblock(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Unblock a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to unblock.

        Returns:
            A dictionary confirming the group unblock.

        """
        response = await self._make_request(
            "DELETE", f"/v1/groups/{phone_number}/{group_id}/block"
        )
        return cast("dict[str, Any]", response)

    async def join(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Join a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to join.

        Returns:
            A dictionary confirming the group join.

        """
        response = await self._make_request(
            "POST", f"/v1/groups/{phone_number}/{group_id}/join"
        )
        return cast("dict[str, Any]", response)

    async def add_members(
        self, phone_number: str, group_id: str, request: ChangeGroupMembersRequest
    ) -> dict[str, Any]:
        """Add members to a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to modify.
            request: An object specifying the members to add.

        Returns:
            A dictionary confirming the member addition.

        """
        response = await self._make_request(
            "POST",
            f"/v1/groups/{phone_number}/{group_id}/members",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def remove_members(
        self, phone_number: str, group_id: str, request: ChangeGroupMembersRequest
    ) -> dict[str, Any]:
        """Remove members from a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to modify.
            request: An object specifying the members to remove.

        Returns:
            A dictionary confirming the member removal.

        """
        response = await self._make_request(
            "DELETE",
            f"/v1/groups/{phone_number}/{group_id}/members",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def quit(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Quit a Signal Group.

        Args:
            phone_number: The phone number of the account.
            group_id: The ID of the group to quit.

        Returns:
            A dictionary confirming the group quit.

        """
        response = await self._make_request(
            "POST", f"/v1/groups/{phone_number}/{group_id}/quit"
        )
        return cast("dict[str, Any]", response)
