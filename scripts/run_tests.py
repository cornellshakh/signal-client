from __future__ import annotations

import os
import sys
from typing import NoReturn

try:
    import pytest
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    error_message = "pytest is not installed in the current environment"
    raise RuntimeError(error_message) from exc


def _exit_process(exit_code: int) -> NoReturn:
    os._exit(exit_code)


def main() -> None:
    exit_code = pytest.main(sys.argv[1:])
    _exit_process(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
