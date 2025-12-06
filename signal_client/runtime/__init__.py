"""Runtime primitives for message ingestion and dispatch."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signal_client.runtime.command_router import CommandRouter
    from signal_client.runtime.listener import BackpressurePolicy, MessageService
    from signal_client.runtime.models import QueuedMessage
    from signal_client.runtime.worker_pool import (
        MiddlewareCallable,
        Worker,
        WorkerConfig,
        WorkerPool,
    )

__all__ = [
    "BackpressurePolicy",
    "CommandRouter",
    "MessageService",
    "MiddlewareCallable",
    "QueuedMessage",
    "Worker",
    "WorkerConfig",
    "WorkerPool",
]


def __getattr__(name: str) -> object:
    if name == "CommandRouter":
        from signal_client.runtime.command_router import CommandRouter  # noqa: PLC0415

        return CommandRouter
    if name in {"BackpressurePolicy", "MessageService"}:
        from signal_client.runtime.listener import (  # noqa: PLC0415
            BackpressurePolicy,
            MessageService,
        )

        return BackpressurePolicy if name == "BackpressurePolicy" else MessageService
    if name == "QueuedMessage":
        from signal_client.runtime.models import QueuedMessage  # noqa: PLC0415

        return QueuedMessage
    if name in {
        "MiddlewareCallable",
        "Worker",
        "WorkerConfig",
        "WorkerPool",
    }:
        from signal_client.runtime.worker_pool import (  # noqa: PLC0415
            MiddlewareCallable,
            Worker,
            WorkerConfig,
            WorkerPool,
        )

        return {
            "MiddlewareCallable": MiddlewareCallable,
            "Worker": Worker,
            "WorkerConfig": WorkerConfig,
            "WorkerPool": WorkerPool,
        }[name]
    raise AttributeError(name)
