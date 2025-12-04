import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

DEFAULT_REDACTED_KEYS = frozenset({"message", "body", "text", "name"})
REDACTION_PLACEHOLDER = "[REDACTED]"


class PIIRedactingProcessor:
    def __init__(
        self,
        redact_keys: frozenset[str] = DEFAULT_REDACTED_KEYS,
        placeholder: str = REDACTION_PLACEHOLDER,
    ) -> None:
        self.redact_keys = redact_keys
        self.placeholder = placeholder

    def __call__(
        self, logger: Any, method_name: str, event_dict: EventDict
    ) -> EventDict:
        for key in self.redact_keys:
            if key in event_dict:
                event_dict[key] = self.placeholder
        return event_dict


class _StructlogGuard:
    _configured = False

    @classmethod
    def ensure_configured(
        cls,
        *,
        json_output: bool = False,
        redaction_enabled: bool = True,
    ) -> None:
        """
        Configure structlog only if the caller has not already configured it.
        Defaults to a concise console renderer; opt into JSON by setting
        json_output=True.
        """
        if cls._configured:
            return
        if getattr(structlog, "is_configured", lambda: False)():
            cls._configured = True
            return

        # Processors for structlog before it hands off to standard logging.
        processors: list[Processor] = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]
        if redaction_enabled:
            processors.append(PIIRedactingProcessor())
        processors.append(structlog.stdlib.render_to_log_kwargs)

        structlog.configure(
            processors=processors,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Configure the standard library logger.
        renderer: Processor
        if json_output:
            renderer = structlog.processors.JSONRenderer()
        else:
            renderer = structlog.dev.ConsoleRenderer(
                colors=True, exception_formatter=structlog.dev.plain_traceback
            )

        formatter = structlog.stdlib.ProcessorFormatter(
            # These run on ALL entries, including those from other libraries.
            foreign_pre_chain=[
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
            ],
            # These run on entries from structlog.
            processor=renderer,
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()

        # Clear existing handlers to avoid duplicate logging.
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)

        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

        cls._configured = True

    @classmethod
    def reset(cls) -> None:
        cls._configured = False


def ensure_structlog_configured(
    *,
    json_output: bool = False,
    redaction_enabled: bool = True,
) -> None:
    """Idempotently configure structlog unless already configured externally."""
    _StructlogGuard.ensure_configured(
        json_output=json_output,
        redaction_enabled=redaction_enabled,
    )


def reset_structlog_configuration_guard() -> None:
    """Reset the guard flag; intended for tests that manipulate structlog directly."""
    _StructlogGuard.reset()


__all__ = [
    "ensure_structlog_configured",
    "reset_structlog_configuration_guard",
    "PIIRedactingProcessor",
]
