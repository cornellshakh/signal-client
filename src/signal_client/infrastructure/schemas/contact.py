from __future__ import annotations

from pydantic import BaseModel


class Contact(BaseModel):
    uuid: str
    number: str
    name: str
    color: str
    blocked: bool = False
