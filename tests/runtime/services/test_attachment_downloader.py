"""Tests for the attachment downloader service."""

from __future__ import annotations

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import aiohttp
import pytest

from signal_client.adapters.api import AttachmentsClient, base_client
from signal_client.adapters.api.schemas.message import AttachmentPointer
from signal_client.runtime.services.attachment_downloader import (
    AttachmentDownloader,
    AttachmentDownloadError,
)


class _FakeAttachmentsClient(AttachmentsClient):
    def __init__(
        self,
        blobs: dict[str, bytes],
        client_config: base_client.ClientConfig | None = None,
    ) -> None:
        if client_config is None:
            dummy_session = cast(
                "aiohttp.ClientSession",
                MagicMock(spec=aiohttp.ClientSession),
            )
            client_config = base_client.ClientConfig(
                session=dummy_session,
                base_url="http://fake-url.com",
            )
        super().__init__(client_config)
        self._blobs = blobs

    async def get_attachment(self, attachment_id: str) -> bytes:
        return self._blobs[attachment_id]

    # Required by BaseClient, even if not used in this test
    async def _make_request(self, method: str, path: str, **kwargs: object) -> bytes:
        raise NotImplementedError("This method should not be called in these tests")


@pytest.mark.asyncio
async def test_download_and_cleanup_tempdir(tmp_path: Path) -> None:
    """Test downloading attachments and cleaning up temporary directory."""
    attachments = [
        AttachmentPointer(id="one", filename="one.txt"),
        AttachmentPointer(id="two"),
    ]
    client: AttachmentsClient = _FakeAttachmentsClient({"one": b"1", "two": b"22"})
    downloader = AttachmentDownloader(client, max_total_bytes=10)

    async with downloader.download(attachments) as files:
        assert [file.name for file in files] == ["one.txt", "two"]
        for file in files:
            assert file.exists()
            assert file.read_bytes()

    for file in files:
        assert not file.exists()
        assert not file.parent.exists()


@pytest.mark.asyncio
async def test_download_with_destination_dir(tmp_path: Path) -> None:
    """Test downloading attachments to a specified destination directory."""
    attachments = [AttachmentPointer(id="one", filename="keep.bin")]
    client: AttachmentsClient = _FakeAttachmentsClient({"one": b"123"})
    downloader = AttachmentDownloader(client)

    dest = tmp_path / "attachments"
    async with downloader.download(attachments, dest_dir=dest) as files:
        assert files[0].parent == dest
        assert files[0].read_bytes() == b"123"

    # Caller-managed destination should remain intact.
    assert dest.exists()
    assert (dest / "keep.bin").exists()


@pytest.mark.asyncio
async def test_download_exceeds_limit(tmp_path: Path) -> None:
    """Test that downloading attachments exceeding the size limit raises an error."""
    attachments = [AttachmentPointer(id="one", filename="large.bin")]
    client: AttachmentsClient = _FakeAttachmentsClient({"one": b"x" * 5})
    downloader = AttachmentDownloader(client, max_total_bytes=1)

    with pytest.raises(AttachmentDownloadError):
        async with downloader.download(attachments) as _:
            pass
