"""Expose lightweight liveness/readiness endpoints for the Signal client."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import structlog
from aiohttp import web

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from signal_client.app.application import Application

log = structlog.get_logger()


class HealthServer:
    """Expose lightweight liveness/readiness/DLQ inspection endpoints."""

    def __init__(
        self,
        application: Application,
        *,
        host: str = "127.0.0.1",
        port: int = 8081,
    ) -> None:
        """Initialize the health server."""
        self._application = application
        self._host = host
        self._port = port
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    async def start(self) -> HealthServer:
        """Start the HTTP server if not already running."""
        if self._runner is not None:
            return self

        app = web.Application()
        app["application"] = self._application
        app.add_routes(
            [
                web.get("/live", self._liveness),
                web.get("/ready", self._readiness),
                web.get("/dlq", self._dlq_status),
            ]
        )
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self._host, self._port)
        await self._site.start()
        log.info(
            "health_server.started",
            host=self._host,
            port=self._port,
        )
        return self

    async def stop(self) -> None:
        """Stop the HTTP server if running."""
        if self._runner is None:
            return
        await self._runner.cleanup()
        self._runner = None
        self._site = None
        log.info("health_server.stopped")

    @staticmethod
    async def _liveness(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    @staticmethod
    async def _readiness(request: web.Request) -> web.Response:
        application: Application = request.app["application"]
        payload = _readiness_payload(application)
        status = 200 if payload["ready"] else 503
        return web.json_response(payload, status=status)

    @staticmethod
    async def _dlq_status(request: web.Request) -> web.Response:
        application: Application = request.app["application"]
        dlq = application.dead_letter_queue
        if dlq is None:
            return web.json_response({"enabled": False, "depth": 0})

        entries = await dlq.inspect()
        depth = len(entries)
        next_retry_candidates: list[float] = list(_next_retry_times(entries))
        next_retry_at = min(next_retry_candidates) if next_retry_candidates else None
        payload = {
            "enabled": True,
            "depth": depth,
            "oldest_next_retry_at": next_retry_at,
        }
        return web.json_response(payload)


def _readiness_payload(application: Application) -> dict[str, Any]:
    queue_ready = application.queue is not None
    worker_pool_ready = application.worker_pool is not None
    websocket_configured = application.websocket_client is not None
    api_clients_ready = application.api_clients is not None
    intake_snapshot = (
        application.intake_controller.snapshot()
        if application.intake_controller is not None
        else None
    )
    ready = (
        queue_ready and worker_pool_ready and websocket_configured and api_clients_ready
    )
    queue_depth = application.queue.qsize() if application.queue is not None else None
    return {
        "ready": ready,
        "queue_ready": queue_ready,
        "worker_pool_ready": worker_pool_ready,
        "websocket_configured": websocket_configured,
        "api_clients_ready": api_clients_ready,
        "queue_depth": queue_depth,
        "ingest_paused_until": (
            intake_snapshot.get("paused_until") if intake_snapshot else None
        ),
    }


async def start_health_server(
    application: Application,
    *,
    host: str = "127.0.0.1",
    port: int = 8081,
) -> HealthServer:
    """Create and start a HealthServer for the given application."""
    server = HealthServer(application, host=host, port=port)
    await server.start()
    return server


def _next_retry_times(entries: Iterable[dict[str, Any]]) -> Iterable[float]:
    """Extract numeric next-retry timestamps from DLQ entries."""
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        candidate = entry.get("next_retry_at")
        if isinstance(candidate, (int, float)):
            yield float(candidate)


__all__ = ["HealthServer", "start_health_server"]
