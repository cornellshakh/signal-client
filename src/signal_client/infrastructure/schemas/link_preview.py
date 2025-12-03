from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class LinkPreview(BaseModel):
    base64_thumbnail: str | None = None
    title: str | None = None
    description: str | None = None
    url: str

    model_config = ConfigDict(populate_by_name=True)
