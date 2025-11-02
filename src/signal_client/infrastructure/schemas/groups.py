from __future__ import annotations

from pydantic import BaseModel


class GroupPermissions(BaseModel):
    add_members: str
    edit_details: str


class CreateGroupRequest(BaseModel):
    name: str
    members: list[str]
    description: str | None = None
    permissions: GroupPermissions | None = None
    group_link: str | None = None
    expiration_time: int | None = None


class UpdateGroupRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    base64_avatar: str | None = None
    expiration_time: int | None = None
    group_link: str | None = None
    permissions: GroupPermissions | None = None


class ChangeGroupMembersRequest(BaseModel):
    members: list[str]


class ChangeGroupAdminsRequest(BaseModel):
    admins: list[str]
