"""Service for downloading and managing attachments."""

from __future__ import annotations

import tempfile
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from signal_client.adapters.api.attachments_client import AttachmentsClient
from signal_client.adapters.api.schemas.message import AttachmentPointer
from signal_client.core.exceptions import SignalAPIError

DEFAULT_MAX_TOTAL_BYTES = 25 * 1024 * 1024


class AttachmentDownloadError(Exception):
    """Raised when attachments cannot be downloaded."""


class AttachmentDownloader:
    """Download attachments to disk with size limits and optional cleanup."""

    def __init__(
        self,
        attachments_client: AttachmentsClient,
        *,
        max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    ) -> None:
        """Initialize the AttachmentDownloader.

        Args:
            attachments_client: The client for interacting with attachment APIs.
            max_total_bytes: The maximum total size of all attachments to download.

        """
        self._attachments_client = attachments_client
        self._max_total_bytes = max_total_bytes

    @property
    def max_total_bytes(self) -> int:
        """The maximum total size of all attachments to download."""
        return self._max_total_bytes

    @asynccontextmanager
    async def download(
        self,
        attachments: Sequence[AttachmentPointer],
        *,
        dest_dir: str | Path | None = None,
    ) -> AsyncIterator[list[Path]]:
        """Download attachments and optionally clean them up on exit."""
        if not attachments:
            yield []
            return

        temp_dir: tempfile.TemporaryDirectory[str] | None = None
        base_dir: Path
        if dest_dir is None:
            temp_dir = tempfile.TemporaryDirectory(prefix="signal-attachments-")
            base_dir = Path(temp_dir.name)
        else:
            base_dir = Path(dest_dir)
            base_dir.mkdir(parents=True, exist_ok=True)

        total_bytes = 0
        paths: list[Path] = []
        try:
            for attachment in attachments:
                if not attachment.id:
                    continue
                try:
                    content = await self._attachments_client.get_attachment(
                        attachment.id
                    )
                except SignalAPIError as e:
                    message = f"Failed to download attachment {attachment.id}: {e}"
                    raise AttachmentDownloadError(message) from e

                total_bytes += len(content)
                if total_bytes > self._max_total_bytes:
                    message = (
                        f"total attachment size {total_bytes} exceeds "
                        f"limit {self._max_total_bytes} bytes"
                    )
                    raise AttachmentDownloadError(message)

                filename = attachment.filename or attachment.id
                path = base_dir / filename
                path.write_bytes(content)
                paths.append(path)

            yield paths
        finally:
            if temp_dir is not None:
                for path in paths:
                    with suppress(FileNotFoundError):
                        path.unlink()
                with suppress(
                    OSError
                ):  # Directory may not be empty or already removed.
                    base_dir.rmdir()
                temp_dir.cleanup()


__all__ = [
    "DEFAULT_MAX_TOTAL_BYTES",
    "AttachmentDownloadError",
    "AttachmentDownloader",
]
