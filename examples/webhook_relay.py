r"""Accept JSON payloads over HTTP and relay them to Signal recipients.

Requirements:
- A running `signal-cli-rest-api` instance
- Environment: SIGNAL_PHONE_NUMBER, SIGNAL_SERVICE_URL, SIGNAL_API_URL

Run:
    poetry run python examples/webhook_relay.py
Then POST:
    curl -X POST http://localhost:8081/relay \
      -H 'Content-Type: application/json' \
      -d '{"recipients": ["+15551234567"], "message": "Hello from webhook relay"}'
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import signal
from collections.abc import Iterable

from aiohttp import ContentTypeError, web

from signal_client.app import Application
from signal_client.core.config import Settings


def _normalize_recipients(raw: object) -> list[str]:
    if isinstance(raw, str):
        normalized = raw.strip()
        return [normalized] if normalized else []
    if isinstance(raw, Iterable):
        recipients: list[str] = []
        for item in raw:
            text = str(item).strip()
            if text:
                recipients.append(text)
        return recipients
    return []


async def main() -> None:
    """Start a small webhook server that relays messages to Signal."""
    settings = Settings.from_sources()  # (1)
    application = Application(settings)
    await application.initialize()  # (2)
    if application.api_clients is None:
        message = "API clients failed to initialize"
        raise RuntimeError(message)

    async def _health(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def _relay(request: web.Request) -> web.Response:
        try:
            payload = await request.json()  # (3)
        except (json.JSONDecodeError, ContentTypeError):
            return web.json_response({"error": "invalid json body"}, status=400)

        message = str(payload.get("message") or "Hello from webhook relay")
        recipients = _normalize_recipients(payload.get("recipients"))
        if not recipients:
            recipients = [settings.phone_number]

        send_payload = {
            "number": settings.phone_number,
            "recipients": recipients,
            "message": message,
        }
        await application.api_clients.messages.send(send_payload)  # (4)
        return web.json_response({"status": "sent", "recipients": recipients})

    web_app = web.Application()
    web_app.add_routes(
        [
            web.get("/health", _health),
            web.post("/relay", _relay),
        ]
    )
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8081)
    await site.start()  # (5)
    print("Webhook relay listening on http://127.0.0.1:8081/relay")

    stop_event = asyncio.Event()

    def _signal_stop() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, _signal_stop)

    try:
        await stop_event.wait()
    finally:
        await runner.cleanup()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
