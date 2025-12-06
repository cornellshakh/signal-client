"""Configuration model and helpers for the Signal client."""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Self

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError


class Settings(BaseSettings):
    """Single, explicit configuration surface for the Signal client.

    Settings are loaded from environment variables and an optional .env file.
    All settings can be overridden via constructor arguments.
    """

    phone_number: str = Field(..., validation_alias="SIGNAL_PHONE_NUMBER")
    signal_service: str = Field(..., validation_alias="SIGNAL_SERVICE_URL")
    base_url: str = Field(..., validation_alias="SIGNAL_API_URL")

    api_retries: int = Field(
        3, description="Number of times to retry API requests on transient errors."
    )
    api_backoff_factor: float = Field(
        0.5, description="Factor for exponential backoff between API retries."
    )
    api_timeout: int = Field(
        30, description="Default timeout (in seconds) for API requests."
    )
    api_auth_token: str | None = Field(
        default=None,
        validation_alias="SIGNAL_API_TOKEN",
        description="API authentication token.",
    )
    api_auth_scheme: str = Field(
        "Bearer",
        description="Authentication scheme (e.g., 'Bearer') for the API token.",
    )
    api_default_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Default headers to send with all API requests.",
    )
    api_endpoint_timeouts: dict[str, float] = Field(
        default_factory=dict,
        description="Per-endpoint timeout overrides (e.g., {'/messages': 60}).",
    )
    api_idempotency_header: str = Field(
        "Idempotency-Key", description="Header name for idempotency keys."
    )

    queue_size: int = Field(
        1000, description="Maximum number of messages to queue for processing."
    )
    worker_pool_size: int = Field(
        4, description="Number of worker tasks to process messages concurrently."
    )
    worker_shard_count: int = Field(
        0,
        description="Number of shards for worker pool. "
        "Defaults to worker_pool_size if 0.",
    )
    queue_put_timeout: float = Field(
        1.0, description="Timeout (in seconds) for putting messages into the queue."
    )
    queue_drop_oldest_on_timeout: bool = Field(
        default=True,
        description="If True, drop oldest message if queue is full and put times out.",
    )
    durable_queue_enabled: bool = Field(
        default=False, description="Enable persistent queueing for messages."
    )
    durable_queue_max_length: int = Field(
        10000, description="Maximum length of the durable queue."
    )
    ingest_checkpoint_window: int = Field(
        5000, description="Number of messages after which to save ingest checkpoint."
    )
    ingest_queue_name: str = Field(
        "signal_client_ingest",
        description="Name of the ingest queue in persistent storage.",
    )
    ingest_checkpoint_key: str = Field(
        "signal_client_ingest_checkpoint",
        description="Key for storing ingest checkpoint in persistent storage.",
    )
    ingest_pause_seconds: float = Field(
        1.0, description="Default duration (in seconds) to pause message ingestion."
    )
    distributed_locks_enabled: bool = Field(
        default=False, description="Enable distributed locking for worker coordination."
    )
    distributed_lock_timeout: int = Field(
        30, description="Timeout (in seconds) for acquiring distributed locks."
    )

    rate_limit: int = Field(
        50, description="Maximum number of API requests per rate_limit_period."
    )
    rate_limit_period: int = Field(
        1, description="Time window (in seconds) for rate limiting."
    )
    websocket_path: str | None = Field(
        default=None,
        validation_alias="SIGNAL_WS_PATH",
        description="WebSocket path for Signal service.",
    )

    circuit_breaker_failure_threshold: int = Field(
        5, description="Number of failures before circuit opens."
    )
    circuit_breaker_reset_timeout: int = Field(
        30, description="Time (in seconds) before a half-open state is attempted."
    )
    circuit_breaker_failure_rate_threshold: float = Field(
        0.5, description="Failure rate threshold (0.0-1.0) to open the circuit."
    )
    circuit_breaker_min_requests_for_rate_calc: int = Field(
        10, description="Minimum requests needed to calculate failure rate."
    )

    storage_type: str = Field(
        "memory", description="Type of storage backend: 'memory', 'sqlite', or 'redis'."
    )
    redis_host: str = Field(
        "localhost", description="Redis host for 'redis' storage type."
    )
    redis_port: int = Field(6379, description="Redis port for 'redis' storage type.")
    sqlite_database: str = Field(
        "signal_client.db",
        description="SQLite database file for 'sqlite' storage type.",
    )

    dlq_name: str = Field(
        "signal_client_dlq",
        description="Name of the Dead Letter Queue in persistent storage.",
    )
    dlq_max_retries: int = Field(
        5, description="Maximum number of retries for messages in the DLQ."
    )

    log_redaction_enabled: bool = Field(
        default=True, description="Enable or disable PII redaction in logs."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_storage(self) -> Self:
        """Validate storage-related settings based on the chosen storage_type.

        Ensures that required fields for 'redis' and 'sqlite' storage are provided
        and that numeric fields have valid positive values.

        Raises:
            ValueError: If storage configuration is invalid.

        Returns:
            The validated Settings instance.

        """
        self._validate_storage_type()
        self._validate_queue_limits()
        self._normalize_worker_shards()
        self._validate_endpoint_timeouts()
        self._ensure_idempotency_header()
        return self

    def _validate_storage_type(self) -> None:
        storage_type = self.storage_type.lower()
        validators = {
            "redis": self._validate_redis_storage,
            "sqlite": self._validate_sqlite_storage,
            "memory": lambda: None,
        }
        validator = validators.get(storage_type)
        if validator is None:
            message = f"Unsupported storage_type '{self.storage_type}'."
            raise ValueError(message)
        validator()

    def _validate_redis_storage(self) -> None:
        if not self.redis_host:
            message = "Redis storage requires 'redis_host'."
            raise ValueError(message)
        if self.redis_port is None:
            message = "Redis storage requires 'redis_port'."
            raise ValueError(message)
        if isinstance(self.redis_port, int) and self.redis_port <= 0:
            message = "'redis_port' must be a positive integer."
            raise ValueError(message)

    def _validate_sqlite_storage(self) -> None:
        if not self.sqlite_database:
            message = "SQLite storage requires 'sqlite_database'."
            raise ValueError(message)

    def _validate_queue_limits(self) -> None:
        if self.durable_queue_max_length <= 0:
            message = "'durable_queue_max_length' must be positive."
            raise ValueError(message)
        if self.ingest_checkpoint_window <= 0:
            message = "'ingest_checkpoint_window' must be positive."
            raise ValueError(message)
        if self.ingest_pause_seconds < 0:
            message = "'ingest_pause_seconds' must be non-negative."
            raise ValueError(message)
        if self.distributed_lock_timeout <= 0:
            message = "'distributed_lock_timeout' must be positive."
            raise ValueError(message)

    def _normalize_worker_shards(self) -> None:
        if (
            self.worker_shard_count <= 0
            or self.worker_shard_count > self.worker_pool_size
        ):
            self.worker_shard_count = self.worker_pool_size

    def _validate_endpoint_timeouts(self) -> None:
        for path, timeout in self.api_endpoint_timeouts.items():
            if timeout is None or float(timeout) <= 0:
                message = (
                    f"'api_endpoint_timeouts' entry for '{path}' must be positive."
                )
                raise ValueError(message)

    def _ensure_idempotency_header(self) -> None:
        if not self.api_idempotency_header:
            message = "'api_idempotency_header' cannot be empty."
            raise ValueError(message)

    @classmethod
    def from_sources(cls: type[Self], config: dict[str, Any] | None = None) -> Self:
        """Load settings from environment variables and an optional dictionary.

        Args:
            config: An optional dictionary to override environment-loaded settings.

        Raises:
            ConfigurationError: If any required settings are missing or invalid.

        Returns:
            A validated Settings instance.

        """
        try:
            env_payload: dict[str, Any] = {}
            try:
                env_payload = cls().model_dump()  # type: ignore[call-arg]
            except ValidationError:
                env_payload = {}

            payload: dict[str, Any] = (
                env_payload if config is None else {**env_payload, **config}
            )
            with _without_required_env():
                settings = cls.model_validate(payload)
            cls._validate_required_fields(settings)
        except ValidationError as validation_error:
            raise cls._wrap_validation_error(validation_error) from validation_error
        else:
            return settings

    @classmethod
    def _wrap_validation_error(cls, error: ValidationError) -> ConfigurationError:
        """Wrap a Pydantic ValidationError in a custom ConfigurationError.

        Args:
            error: The original Pydantic ValidationError.

        Returns:
            A ConfigurationError with a more user-friendly message.

        """

        def _error_field(err: Mapping[str, object]) -> str:
            loc = err.get("loc")
            if not isinstance(loc, (list, tuple)):
                return ""
            return str(loc[-1]) if loc else ""

        missing = cls._missing_fields(error)
        errors = error.errors(include_url=False)
        fields = {_error_field(err) for err in errors if _error_field(err)}
        invalid_fields = sorted(fields - {field.split("/")[-1] for field in missing})
        invalid_errors = [err for err in errors if _error_field(err) in invalid_fields]

        if missing and invalid_fields:
            missing_list = ", ".join(sorted(missing))
            invalid_list = ", ".join(invalid_fields)
            first_error = (
                invalid_errors[0]["msg"] if invalid_errors else errors[0]["msg"]
            )
            message = (
                f"Invalid configuration overrides. Missing: {missing_list}. "
                f"Invalid: {invalid_list} ({first_error})."
            )
            return ConfigurationError(message)

        if missing:
            missing_list = ", ".join(sorted(missing))
            message = f"Missing required configuration values: {missing_list}."
            return ConfigurationError(message)

        first_error = errors[0]["msg"]
        field_list = ", ".join(sorted(fields)) if fields else "configuration"
        message = f"Invalid configuration for {field_list}: {first_error}."
        return ConfigurationError(message)

    @classmethod
    def _missing_fields(cls, error: ValidationError) -> set[str]:
        """Extract missing field names from a Pydantic ValidationError.

        Args:
            error: The Pydantic ValidationError instance.

        Returns:
            A set of strings representing the names of missing fields.

        """
        missing: set[str] = set()
        for err in error.errors(include_url=False):
            if err.get("type") not in {"missing", "value_error.missing"}:
                continue
            loc = err.get("loc")
            if not loc:
                continue
            field_name = str(loc[-1])
            alias = cls._env_alias_for_field(field_name)
            missing.add(alias or field_name)
        return missing

    @classmethod
    def _env_alias_for_field(cls, field_name: str) -> str | None:
        """Get the environment variable alias for a given field name.

        Args:
            field_name: The name of the setting field.

        Returns:
            The environment variable alias if found, otherwise None.

        """
        field = cls.model_fields.get(field_name)
        if not field:
            return None
        alias = field.validation_alias
        if not alias:
            return None
        return (
            str(alias)
            if not isinstance(alias, tuple)
            else "/".join(str(item) for item in alias)
        )

    @classmethod
    def _validate_required_fields(cls, settings: Self) -> None:
        """Validate that essential required fields are present.

        Args:
            settings: The Settings instance to validate.

        Raises:
            ConfigurationError: If any essential required fields are missing.

        """
        missing = [
            field
            for field in ("phone_number", "signal_service", "base_url")
            if not getattr(settings, field)
        ]
        if missing:
            missing_list = ", ".join(missing)
            message = f"Missing required configuration values: {missing_list}."
            raise ConfigurationError(message)


@contextmanager
def _without_required_env() -> Iterator[None]:
    required_envs = {
        "SIGNAL_PHONE_NUMBER",
        "SIGNAL_SERVICE_URL",
        "SIGNAL_API_URL",
    }
    preserved = {key: os.environ.get(key) for key in required_envs}
    for key in required_envs:
        os.environ.pop(key, None)
    try:
        yield
    finally:
        for key, value in preserved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
