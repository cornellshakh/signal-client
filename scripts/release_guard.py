from __future__ import annotations

import sys
from pathlib import Path
from shutil import which
from subprocess import CalledProcessError, run  # nosec B404

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from signal_client.release_guard import enforce_pre_release_policy


def _read_version() -> str:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    return pyproject["tool"]["poetry"]["version"]


def _recent_commit_messages(limit: int = 50) -> list[str]:
    git_executable = which("git")
    if git_executable is None:
        return []

    try:
        result = run(  # noqa: S603  # nosec B603
            [git_executable, "log", f"-{limit}", "--pretty=%B%x1f"],
            check=True,
            capture_output=True,
            text=True,
        )
    except CalledProcessError:
        return []

    raw = result.stdout.strip("\x1f\n")
    if not raw:
        return []
    return [message.strip() for message in raw.split("\x1f") if message.strip()]


def main() -> None:
    version = _read_version()
    commits = _recent_commit_messages()

    try:
        enforce_pre_release_policy(version, commits)
    except RuntimeError as exc:  # pragma: no cover - CLI surface
        sys.stderr.write(f"release-guard: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
