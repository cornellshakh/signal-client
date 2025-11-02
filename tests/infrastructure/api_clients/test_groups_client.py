from __future__ import annotations

from typing import Any

import pytest

from signal_client.domain.groups import (
    ChangeGroupAdminsRequest,
    ChangeGroupMembersRequest,
    CreateGroupRequest,
    UpdateGroupRequest,
)
from signal_client.infrastructure.api_clients.groups_client import GroupsClient


@pytest.mark.asyncio
async def test_create_group(
    groups_client: GroupsClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    request = CreateGroupRequest(name="Test Group", members=[phone_number])
    aresponses.add(
        "localhost:8080",
        f"/v1/groups/{phone_number}",
        "POST",
        aresponses.Response(status=201),
    )
    await groups_client.create_group(phone_number, request)


@pytest.mark.asyncio
async def test_update_group(
    groups_client: GroupsClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    group_id = "group_id"
    request = UpdateGroupRequest(name="New Name")
    aresponses.add(
        "localhost:8080",
        f"/v1/groups/{phone_number}/{group_id}",
        "PUT",
        aresponses.Response(status=204),
    )
    await groups_client.update_group(phone_number, group_id, request)


@pytest.mark.asyncio
async def test_add_members(
    groups_client: GroupsClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    group_id = "group_id"
    request = ChangeGroupMembersRequest(members=[phone_number])
    aresponses.add(
        "localhost:8080",
        f"/v1/groups/{phone_number}/{group_id}/members",
        "POST",
        aresponses.Response(status=204),
    )
    await groups_client.add_members(phone_number, group_id, request)


@pytest.mark.asyncio
async def test_remove_members(
    groups_client: GroupsClient, aresponses: Any
) -> None:
    phone_number = "+1234567890"
    group_id = "group_id"
    request = ChangeGroupMembersRequest(members=[phone_number])
    aresponses.add(
        "localhost:8080",
        f"/v1/groups/{phone_number}/{group_id}/members",
        "DELETE",
        aresponses.Response(status=204),
    )
    await groups_client.remove_members(phone_number, group_id, request)


@pytest.mark.asyncio
async def test_add_admins(groups_client: GroupsClient, aresponses: Any) -> None:
    phone_number = "+1234567890"
    group_id = "group_id"
    request = ChangeGroupAdminsRequest(admins=[phone_number])
    aresponses.add(
        "localhost:8080",
        f"/v1/groups/{phone_number}/{group_id}/admins",
        "POST",
        aresponses.Response(status=204),
    )
    await groups_client.add_admins(phone_number, group_id, request)
