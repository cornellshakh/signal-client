from __future__ import annotations

from collections.abc import Iterable

from prometheus_client import REGISTRY, CollectorRegistry, start_http_server


def start_metrics_server(
    port: int = 8000,
    addr: str = "127.0.0.1",
    *,
    registry: CollectorRegistry = REGISTRY,
) -> object:
    """
    Start a minimal HTTP server that exposes Prometheus metrics.

    Returns the server object so callers can stop it if desired.
    """
    return start_http_server(port, addr=addr, registry=registry)


__all__: Iterable[str] = ["start_metrics_server"]
