from __future__ import annotations

from pydantic import BaseModel


class LinkPreview(BaseModel):
    url: str
    title: str
    description: str | None = None
    image: str | None = None
