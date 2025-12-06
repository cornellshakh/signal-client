"""Service module for signal_client."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from signal_client.runtime.listener import BackpressurePolicy, MessageService
    from signal_client.runtime.services.worker_pool_manager import (
        CommandRouter,
        MiddlewareCallable,
        Worker,
        WorkerConfig,
        WorkerPool,
        WorkerPoolManager,
    )

__all__ = [
    "BackpressurePolicy",
    "CommandRouter",
    "MessageService",
    "MiddlewareCallable",
    "Worker",
    "WorkerConfig",
    "WorkerPool",
    "WorkerPoolManager",
]


def __getattr__(name: str) -> object:
    if name in {"BackpressurePolicy", "MessageService"}:
        from signal_client.runtime.listener import (  # noqa: PLC0415
            BackpressurePolicy,
            MessageService,
        )

        return BackpressurePolicy if name == "BackpressurePolicy" else MessageService
    if name in {
        "CommandRouter",
        "MiddlewareCallable",
        "Worker",
        "WorkerConfig",
        "WorkerPool",
        "WorkerPoolManager",
    }:
        from signal_client.runtime.services import (  # noqa: PLC0415
            worker_pool_manager as manager,
        )

        return getattr(manager, name)
    raise AttributeError(name)
