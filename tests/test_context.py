from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock

import pytest

from signal_client import SignalClient
from signal_client.context import Context
from signal_client.context_deps import ContextDependencies
from signal_client.infrastructure.schemas.message import Message, MessageType
from signal_client.infrastructure.schemas.requests import SendMessageRequest


def _build_context(
    context_dependencies: ContextDependencies,
    *,
    group: str | None = None,
    text: str = "test",
) -> Context:
    message = Message(
        message=text,
        source="user1",
        timestamp=1,
        type=MessageType.DATA_MESSAGE,
        group={"groupId": group} if group else None,
    )
    return Context(message=message, dependencies=context_dependencies)


@pytest.mark.asyncio
async def test_context_send_defaults_recipient_and_number(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies)
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    send_mock.reset_mock()
    send_mock.return_value = {"timestamp": "5"}

    response = await context.send(SendMessageRequest(message="hello", recipients=[]))

    (request_dict,) = send_mock.call_args.args
    assert request_dict["message"] == "hello"
    assert request_dict["recipients"] == ["user1"]
    assert request_dict["number"] == "+1234567890"
    assert response is not None
    assert response.timestamp == 5


@pytest.mark.asyncio
async def test_reply_text_sets_quote_fields(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies, text="quoted")
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    send_mock.reset_mock()

    await context.reply_text("replying")

    (request_dict,) = send_mock.call_args.args
    assert request_dict["quote_author"] == "user1"
    assert request_dict["quote_message"] == "quoted"
    assert request_dict["quote_timestamp"] == 1
    assert request_dict["recipients"] == ["user1"]


@pytest.mark.asyncio
async def test_send_markdown_sets_text_mode(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies)
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    send_mock.reset_mock()

    await context.send_markdown("**bold**")

    (request_dict,) = send_mock.call_args.args
    assert request_dict["text_mode"] == "styled"


@pytest.mark.asyncio
async def test_send_view_once_sets_flag_and_attachments(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies)
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    send_mock.reset_mock()

    await context.send_view_once(["aGVsbG8="], message="view once payload")

    (request_dict,) = send_mock.call_args.args
    assert request_dict["view_once"] is True
    assert request_dict["base64_attachments"] == ["aGVsbG8="]
    assert request_dict["message"] == "view once payload"


@pytest.mark.asyncio
async def test_send_with_preview_builds_link_preview(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies)
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    send_mock.reset_mock()

    await context.send_with_preview(
        "https://example.com/article",
        title="Example",
        description="Desc",
    )

    (request_dict,) = send_mock.call_args.args
    preview = request_dict["link_preview"]
    assert preview["url"] == "https://example.com/article"
    assert preview["title"] == "Example"
    assert preview["description"] == "Desc"


@pytest.mark.asyncio
async def test_send_sticker_formats_reference(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies)
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    send_mock.reset_mock()

    await context.send_sticker("pack123", 5)

    (request_dict,) = send_mock.call_args.args
    assert request_dict["sticker"] == "pack123:5"


@pytest.mark.asyncio
async def test_send_receipt_targets_group(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies, group="group-1")
    receipts_mock = cast("AsyncMock", bot.api_clients.receipts.send_receipt)
    receipts_mock.reset_mock()

    await context.send_receipt(42, receipt_type="viewed")

    args = receipts_mock.call_args.args
    assert args[0] == "+1234567890"
    payload = args[1]
    assert payload["recipient"] == "group-1"
    assert payload["receipt_type"] == "viewed"
    assert payload["timestamp"] == 42


@pytest.mark.asyncio
async def test_remote_delete_defaults_recipient(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies)
    delete_mock = cast("AsyncMock", bot.api_clients.messages.remote_delete)
    delete_mock.reset_mock()
    delete_mock.return_value = {"timestamp": "99"}

    response = await context.remote_delete(target_timestamp=123)

    _, request_dict = delete_mock.call_args.args
    assert request_dict["recipient"] == "user1"
    assert request_dict["timestamp"] == 123
    assert response is not None
    assert response.timestamp == 99


@pytest.mark.asyncio
async def test_typing_indicator_targets_group(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    context = _build_context(context_dependencies, group="abc")
    typing_mock = cast("AsyncMock", bot.api_clients.messages.set_typing_indicator)
    typing_mock.reset_mock()

    await context.show_typing()

    request_dict = typing_mock.call_args.args[1]
    assert request_dict["recipient"] == "abc"


@pytest.mark.asyncio
async def test_reply_with_quote_mentions_adds_author(
    bot: SignalClient,
    context_dependencies: ContextDependencies,
) -> None:
    # Message text includes the source to allow safe mention offsets.
    context = _build_context(context_dependencies, text="user1 said hello")
    send_mock = cast("AsyncMock", bot.api_clients.messages.send)
    send_mock.reset_mock()

    await context.reply_with_quote_mentions("replying with mention")

    (request_dict,) = send_mock.call_args.args
    mentions = request_dict.get("quote_mentions") or []
    assert len(mentions) == 1
    assert mentions[0]["author"] == "user1"
    assert mentions[0]["start"] == 0
    assert mentions[0]["length"] == len("user1")
