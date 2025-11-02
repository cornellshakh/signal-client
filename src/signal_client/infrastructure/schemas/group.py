from __future__ import annotations

from pydantic import BaseModel


class Group(BaseModel):
    id: str
    name: str
    members: list[str]
    admins: list[str]
    blocked: bool = False
    pending_invites: list[str] = []
    pending_requests: list[str] = []
