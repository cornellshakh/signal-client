from __future__ import annotations

from pydantic import BaseModel


class UpdateProfileRequest(BaseModel):
    name: str
    about: str | None = None
    base64_avatar: str | None = None
