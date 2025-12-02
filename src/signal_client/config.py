from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Self

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError


class Settings(BaseSettings):
    """Single, explicit configuration surface for the Signal client."""

    phone_number: str = Field(..., validation_alias="SIGNAL_PHONE_NUMBER")
    signal_service: str = Field(..., validation_alias="SIGNAL_SERVICE_URL")
    base_url: str = Field(..., validation_alias="SIGNAL_API_URL")

    api_retries: int = 3
    api_backoff_factor: float = 0.5
    api_timeout: int = 30

    queue_size: int = 1000
    worker_pool_size: int = 4
    queue_put_timeout: float = 1.0
    queue_drop_oldest_on_timeout: bool = True

    rate_limit: int = 50
    rate_limit_period: int = 1  # seconds

    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_reset_timeout: int = 30  # seconds
    circuit_breaker_failure_rate_threshold: float = 0.5
    circuit_breaker_min_requests_for_rate_calc: int = 10

    storage_type: str = "sqlite"
    redis_host: str = "localhost"
    redis_port: int = 6379
    sqlite_database: str = "signal_client.db"

    dlq_name: str = "signal_client_dlq"
    dlq_max_retries: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
        case_sensitive=False,
    )

    @model_validator(mode="after")
    def validate_storage(self) -> Self:
        storage_type = self.storage_type.lower()
        if storage_type == "redis":
            if not self.redis_host:
                message = "Redis storage requires 'redis_host'."
                raise ValueError(message)
            if self.redis_port is None:
                message = "Redis storage requires 'redis_port'."
                raise ValueError(message)
            if isinstance(self.redis_port, int) and self.redis_port <= 0:
                message = "'redis_port' must be a positive integer."
                raise ValueError(message)
        elif storage_type == "sqlite":
            if not self.sqlite_database:
                message = "SQLite storage requires 'sqlite_database'."
                raise ValueError(message)
        else:
            message = f"Unsupported storage_type '{self.storage_type}'."
            raise ValueError(message)
        return self

    @classmethod
    def from_sources(cls: type[Self], config: dict[str, Any] | None = None) -> Self:
        """Load settings from environment and optional overrides."""
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
