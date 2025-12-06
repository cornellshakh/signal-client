"""Tests for the AttachmentsClient."""

from __future__ import annotations

from typing import Any

import pytest

from signal_client.adapters.api.attachments_client import (
    AttachmentsClient,
)


@pytest.mark.asyncio
async def test_attachments_client(
    attachments_client: AttachmentsClient,
    aresponses: Any,  # noqa: ANN401
) -> None:
    """Test the attachments client."""
    # Arrange
    aresponses.add(
        "localhost:8080",
        "/v1/attachments",
        "GET",
        aresponses.Response(
            status=200,
            text='[{"id": "attachment1"}]',
            headers={"Content-Type": "application/json"},
        ),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/attachments/attachment1",
        "GET",
        aresponses.Response(status=200, text="attachment data"),
    )
    aresponses.add(
        "localhost:8080",
        "/v1/attachments/attachment1",
        "DELETE",
        aresponses.Response(status=204),
    )

    # Act
    attachments = await attachments_client.get_attachments()
    attachment = await attachments_client.get_attachment("attachment1")
    await attachments_client.remove_attachment("attachment1")

    # Assert
    assert attachments == [{"id": "attachment1"}]
    assert attachment == b"attachment data"
