from __future__ import annotations

from collections.abc import Iterable

from packaging.version import Version

BREAKING_KEYWORDS = (
    "breaking change:",
    "breaking-change:",
    "breaking changes:",
    "breaking-changes:",
)


def is_breaking_change(message: str) -> bool:
    header, *_ = message.splitlines() or [""]
    if "!" in header.split(":", 1)[0]:
        return True

    lowered = message.lower()
    return any(keyword in lowered for keyword in BREAKING_KEYWORDS)


def enforce_pre_release_policy(version: str, commits: Iterable[str]) -> None:
    parsed_version = Version(version)
    if parsed_version.major >= 1:
        return

    offending = [commit for commit in commits if is_breaking_change(commit)]
    if offending:
        lines = "\n".join(f"- {commit.splitlines()[0]}" for commit in offending)
        message = (
            "Breaking changes flagged while project version is < 1.0. "
            "Either bump to 1.x or defer the breaking commit(s):\n"
            f"{lines}"
        )
        raise RuntimeError(message)


__all__ = ["BREAKING_KEYWORDS", "enforce_pre_release_policy", "is_breaking_change"]
