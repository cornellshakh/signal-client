from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from .base_client import BaseClient

if TYPE_CHECKING:
    from signal_client.infrastructure.schemas.groups import (
        ChangeGroupAdminsRequest,
        ChangeGroupMembersRequest,
        CreateGroupRequest,
        UpdateGroupRequest,
    )


class GroupsClient(BaseClient):
    async def get_groups(self, phone_number: str) -> list[dict[str, Any]]:
        """List all Signal Groups."""
        response = await self._make_request("GET", f"/v1/groups/{phone_number}")
        return cast("list[dict[str, Any]]", response)

    async def create_group(
        self, phone_number: str, request: CreateGroupRequest
    ) -> dict[str, Any]:
        """Create a new Signal Group."""
        response = await self._make_request(
            "POST", f"/v1/groups/{phone_number}", json=request.model_dump()
        )
        return cast("dict[str, Any]", response)

    async def get_group(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """List a Signal Group."""
        response = await self._make_request(
            "GET", f"/v1/groups/{phone_number}/{group_id}"
        )
        return cast("dict[str, Any]", response)

    async def update_group(
        self, phone_number: str, group_id: str, request: UpdateGroupRequest
    ) -> dict[str, Any]:
        """Update the state of a Signal Group."""
        response = await self._make_request(
            "PUT",
            f"/v1/groups/{phone_number}/{group_id}",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def delete_group(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Delete a Signal Group."""
        response = await self._make_request(
            "DELETE", f"/v1/groups/{phone_number}/{group_id}"
        )
        return cast("dict[str, Any]", response)

    async def add_admins(
        self, phone_number: str, group_id: str, request: ChangeGroupAdminsRequest
    ) -> dict[str, Any]:
        """Add admins to a group."""
        response = await self._make_request(
            "POST",
            f"/v1/groups/{phone_number}/{group_id}/admins",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def remove_admins(
        self, phone_number: str, group_id: str, request: ChangeGroupAdminsRequest
    ) -> dict[str, Any]:
        """Remove admins from a group."""
        response = await self._make_request(
            "DELETE",
            f"/v1/groups/{phone_number}/{group_id}/admins",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def get_avatar(self, phone_number: str, group_id: str) -> bytes:
        """Returns the avatar of a Signal Group."""
        response = await self._make_request(
            "GET", f"/v1/groups/{phone_number}/{group_id}/avatar"
        )
        return cast("bytes", response)

    async def block(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Block a Signal Group."""
        response = await self._make_request(
            "POST", f"/v1/groups/{phone_number}/{group_id}/block"
        )
        return cast("dict[str, Any]", response)

    async def join(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Join a Signal Group."""
        response = await self._make_request(
            "POST", f"/v1/groups/{phone_number}/{group_id}/join"
        )
        return cast("dict[str, Any]", response)

    async def add_members(
        self, phone_number: str, group_id: str, request: ChangeGroupMembersRequest
    ) -> dict[str, Any]:
        """Add members to a group."""
        response = await self._make_request(
            "POST",
            f"/v1/groups/{phone_number}/{group_id}/members",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def remove_members(
        self, phone_number: str, group_id: str, request: ChangeGroupMembersRequest
    ) -> dict[str, Any]:
        """Remove members from a group."""
        response = await self._make_request(
            "DELETE",
            f"/v1/groups/{phone_number}/{group_id}/members",
            json=request.model_dump(),
        )
        return cast("dict[str, Any]", response)

    async def quit(self, phone_number: str, group_id: str) -> dict[str, Any]:
        """Quit a Signal Group."""
        response = await self._make_request(
            "POST", f"/v1/groups/{phone_number}/{group_id}/quit"
        )
        return cast("dict[str, Any]", response)
