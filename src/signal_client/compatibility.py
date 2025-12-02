from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata

from packaging.version import Version


class CompatibilityError(RuntimeError):
    """Raised when a dependency version is outside the vetted range."""


@dataclass(frozen=True)
class SupportedRange:
    minimum_inclusive: Version
    maximum_exclusive: Version

    def contains(self, version_str: str) -> bool:
        parsed = Version(version_str)
        return self.minimum_inclusive <= parsed < self.maximum_exclusive


SUPPORTED_MATRIX: dict[str, SupportedRange] = {
    "pydantic": SupportedRange(Version("2.12.0"), Version("2.13.0")),
    "structlog": SupportedRange(Version("24.4.0"), Version("24.5.0")),
    "aiohttp": SupportedRange(Version("3.11.9"), Version("4.0.0")),
}


def check_supported_versions() -> None:
    """Ensure installed dependency versions stay within the vetted matrix."""
    for package, supported_range in SUPPORTED_MATRIX.items():
        try:
            installed_version = metadata.version(package)
        except metadata.PackageNotFoundError as exc:  # pragma: no cover - defensive
            message = f"Required package '{package}' is not installed"
            raise CompatibilityError(message) from exc

        if not supported_range.contains(installed_version):
            min_version = supported_range.minimum_inclusive
            max_version = supported_range.maximum_exclusive
            message = (
                f"Package '{package}' is at version '{installed_version}' "
                f"which is outside the vetted range {min_version} to {max_version}"
            )
            raise CompatibilityError(message)


__all__ = [
    "SUPPORTED_MATRIX",
    "CompatibilityError",
    "SupportedRange",
    "check_supported_versions",
]
