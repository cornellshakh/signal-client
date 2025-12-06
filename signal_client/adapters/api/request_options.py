from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(slots=True)
class RequestOptions:
    """Optional parameters to customize a single API request."""

    timeout: float | None = None
    retries: int | None = None
    backoff_factor: float | None = None
    idempotency_key: str | None = None
    headers: Mapping[str, str] | None = None
