from __future__ import annotations

from pydantic import BaseModel


class LinkPreview(BaseModel):
    title: str | None = None
    description: str | None = None
    image: str | None = None
    url: str
