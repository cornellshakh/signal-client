from __future__ import annotations

import structlog


class _StructlogGuard:
    _configured = False

    @classmethod
    def ensure_configured(cls, *, json_output: bool = False) -> None:
        """
        Configure structlog only if the caller has not already configured it.

        Defaults to a concise console renderer; opt into JSON by setting
        json_output=True.
        """
        if cls._configured:
            return

        if getattr(structlog, "is_configured", None) and structlog.is_configured():
            cls._configured = True
            return

        if structlog.get_config():
            cls._configured = True
            return

        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            (
                structlog.processors.JSONRenderer()
                if json_output
                else structlog.dev.ConsoleRenderer()
            ),
        ]
        structlog.configure(processors=processors)  # type: ignore[arg-type]
        cls._configured = True

    @classmethod
    def reset(cls) -> None:
        cls._configured = False


def ensure_structlog_configured(*, json_output: bool = False) -> None:
    """Idempotently configure structlog unless already configured externally."""
    _StructlogGuard.ensure_configured(json_output=json_output)


def reset_structlog_configuration_guard() -> None:
    """Reset the guard flag; intended for tests that manipulate structlog directly."""
    _StructlogGuard.reset()


__all__ = ["ensure_structlog_configured", "reset_structlog_configuration_guard"]
