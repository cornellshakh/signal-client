"""Response schemas used by the Signal client API layer."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ValidationError, field_validator
from typing_extensions import Self

T = TypeVar("T", bound="TimestampedResponse")


class TimestampedResponse(BaseModel):
    """Base response including an optional timestamp."""

    timestamp: int | None = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value: object) -> int | None:
        """Normalize timestamp inputs to integers when possible."""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None

    @classmethod
    def from_raw(cls, payload: object | None) -> Self | None:
        """Attempt to parse a raw payload into a response instance."""
        if payload is None:
            return None

        try:
            return cls.model_validate(payload)
        except ValidationError:
            return None


class SendMessageResponse(TimestampedResponse):
    """Response model for /v2/send."""


class RemoteDeleteResponse(TimestampedResponse):
    """Response model for remote delete."""
