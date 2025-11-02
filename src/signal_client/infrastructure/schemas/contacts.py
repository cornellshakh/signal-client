from __future__ import annotations

from pydantic import BaseModel


class UpdateContactRequest(BaseModel):
    name: str
    number: str
    expiration_in_seconds: int | None = None
