from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import tempfile
from typing import AsyncIterator, Sequence

from signal_client.exceptions import SignalAPIError
from signal_client.infrastructure.api_clients.attachments_client import AttachmentsClient
from signal_client.infrastructure.schemas.message import AttachmentPointer

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
        self._attachments_client = attachments_client
        self._max_total_bytes = max_total_bytes

    @property
    def max_total_bytes(self) -> int:
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
                    raise AttachmentDownloadError(
                        f"Failed to download attachment {attachment.id}: {e}"
                    ) from e

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
                    try:
                        path.unlink()
                    except FileNotFoundError:
                        continue
                try:
                    base_dir.rmdir()
                except OSError:
                    # Directory may not be empty or already removed; best-effort cleanup.
                    pass
                temp_dir.cleanup()


__all__ = [
    "AttachmentDownloadError",
    "AttachmentDownloader",
    "DEFAULT_MAX_TOTAL_BYTES",
]
