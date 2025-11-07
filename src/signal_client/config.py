from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any, Self

from pydantic import Field, ValidationError, model_validator
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigurationError


def _is_missing_error(error: Mapping[str, Any]) -> bool:
    err_type = error.get("type", "")
    msg = error.get("msg", "")
    is_missing_type = err_type in {"missing", "value_error.missing"}
    return is_missing_type or "field required" in msg.lower()


def _field_aliases(field_name: str, model: type[BaseSettings]) -> list[str]:
    field = model.model_fields.get(field_name)
    if field is None:
        return [field_name]

    aliases = _collect_aliases(field)
    if not aliases:
        aliases.append(field_name)
    return list(dict.fromkeys(aliases))


def _collect_aliases(field: FieldInfo) -> list[str]:
    aliases: list[str] = []
    alias = field.validation_alias
    if alias:
        if isinstance(alias, tuple):
            aliases.extend(str(item) for item in alias)
        else:
            aliases.append(str(alias))
    if field.alias:
        aliases.append(str(field.alias))
    return aliases


def _missing_fields_from_error(
    error: ValidationError, model: type[BaseSettings]
) -> list[str]:
    missing = {
        str(err["loc"][-1])
        for err in error.errors(include_url=False)
        if err.get("loc") and _is_missing_error(err)
    }
    return ["/".join(_field_aliases(name, model)) for name in sorted(missing)]


def _env_aliases_for_field(field_name: str, model: type[BaseSettings]) -> list[str]:
    field = model.model_fields.get(field_name)
    if not field or not field.validation_alias:
        return []
    alias = field.validation_alias
    if isinstance(alias, tuple):
        return [str(item) for item in alias]
    return [str(alias)]


@contextmanager
def _temporarily_remove_env(keys: set[str]) -> Iterator[None]:
    if not keys:
        yield
        return

    preserved = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            if key in os.environ:
                del os.environ[key]
        yield
    finally:
        for key, value in preserved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class CoreBotSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    phone_number: str = Field(
        ...,
        validation_alias="SIGNAL_PHONE_NUMBER",
        description="The phone number to use for the Signal client.",
    )
    signal_service: str = Field(
        ...,
        validation_alias="SIGNAL_SERVICE_URL",
        description="The URL of the Signal service.",
    )
    base_url: str = Field(
        ...,
        validation_alias="SIGNAL_API_URL",
        description="The base URL for the Signal API.",
    )


class APISettings(BaseSettings):
    api_retries: int = 3
    api_backoff_factor: float = 0.5
    api_timeout: int = 30


class WorkerSettings(BaseSettings):
    queue_size: int = 1000
    worker_pool_size: int = 4
    queue_put_timeout: float = 1.0
    queue_drop_oldest_on_timeout: bool = True


class RateLimiterSettings(BaseSettings):
    rate_limit: int = 50
    rate_limit_period: int = 1  # seconds


class CircuitBreakerSettings(BaseSettings):
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_reset_timeout: int = 30  # seconds
    circuit_breaker_failure_rate_threshold: float = 0.5
    circuit_breaker_min_requests_for_rate_calc: int = 10


class StorageSettings(BaseSettings):
    storage_type: str = "sqlite"
    redis_host: str = "localhost"
    redis_port: int = 6379
    sqlite_database: str = "signal_client.db"

    @model_validator(mode="after")
    def validate_storage(self) -> StorageSettings:
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


class DLQSettings(BaseSettings):
    dlq_name: str = "signal_client_dlq"
    dlq_max_retries: int = 5


class Settings(
    CoreBotSettings,
    APISettings,
    WorkerSettings,
    RateLimiterSettings,
    CircuitBreakerSettings,
    StorageSettings,
    DLQSettings,
):
    """
    Centralized configuration for the Signal Client.

    This class uses pydantic's BaseSettings to load configuration from
    environment variables and/or a .env file. This provides a robust and
    secure way to manage settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def from_sources(
        cls: type[Self],
        config: dict[str, Any] | None = None,
    ) -> Self:
        base_settings: Self | None = None
        try:
            base_settings = cls()  # type: ignore[call-arg]
        except ValidationError as env_error:
            missing = _missing_fields_from_error(env_error, cls)
            if config is None:
                if missing:
                    missing_list = ", ".join(missing)
                    message = (
                        "Missing required configuration values: "
                        f"{missing_list}. Provide the values via environment variables "
                        "or pass them in the config dictionary."
                    )
                else:
                    message = "Configuration validation failed."
                raise ConfigurationError(message) from env_error

        if config is None:
            if base_settings is None:
                # If we reach here it means environment validation failed but we
                # allowed processing to continue when config is provided; to
                # maintain type safety construct directly and let pydantic raise.
                message = "Configuration validation failed."
                raise ConfigurationError(message)
            return base_settings

        try:
            if base_settings is None:
                aliases = {
                    alias
                    for field in config
                    for alias in _env_aliases_for_field(field, cls)
                }
                with _temporarily_remove_env(aliases):
                    config_payload: Any = config
                    return cls.model_validate(config_payload)

            merged_config = base_settings.model_dump()
            merged_config.update(config)
            aliases = {
                alias
                for field in config
                for alias in _env_aliases_for_field(field, cls)
            }
            with _temporarily_remove_env(aliases):
                merged_payload: Any = merged_config
                return cls.model_validate(merged_payload)
        except ValidationError as config_error:
            missing = _missing_fields_from_error(config_error, cls)
            if missing:
                missing_list = ", ".join(missing)
                message = (
                    "Invalid configuration overrides. Please supply values for: "
                    f"{missing_list}."
                )
            else:
                fields = {
                    str(err["loc"][0])
                    for err in config_error.errors(include_url=False)
                    if err.get("loc")
                }
                field_list = ", ".join(sorted(fields)) if fields else "configuration"
                first_error = config_error.errors(include_url=False)[0]["msg"]
                message = (
                    f"Invalid configuration overrides for {field_list}: {first_error}."
                )
            raise ConfigurationError(message) from config_error
