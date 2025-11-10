from __future__ import annotations

from mkdocs_macros.plugin import MacrosPlugin


DEV_COMMANDS = {
    "ruff": "poetry run ruff check .",
    "black": "poetry run black --check src tests",
    "mypy": "poetry run mypy src",
    "pytest": "poetry run pytest-safe -n auto --cov=signal_client",
    "pytest_quick": "pytest -m \"not performance\"",
    "docs": "poetry run mkdocs serve",
}


def define_env(env: MacrosPlugin) -> None:
    env.variables.update(
        {
            "signal": {
                "package": "signal-client",
                "min_python": "3.11",
                "deployment_targets": "Signal Cloud • Bring Your Own Infrastructure",
            },
            "commands": DEV_COMMANDS,
        }
    )

    @env.macro
    def install_snippet(flavors: str = "pip") -> str:
        command = (
            "pip install signal-client"
            if flavors == "pip"
            else "poetry add signal-client"
        )
        return f"`{command}`"

    @env.macro
    def test_plan_table() -> str:
        header = "| Check | Command | Result |"
        separator = "| --- | --- | --- |"
        rows = [
            ("Ruff", DEV_COMMANDS["ruff"]),
            ("Black", DEV_COMMANDS["black"]),
            ("Mypy", DEV_COMMANDS["mypy"]),
            ("Pytest", DEV_COMMANDS["pytest"]),
            ("Docs", DEV_COMMANDS["docs"]),
        ]
        body = "\n".join(f"| {label} | `{cmd}` | ☐ |" for label, cmd in rows)
        return "\n".join([header, separator, body])

    @env.macro
    def dev_command_list() -> str:
        items = [
            f"- **Ruff:** `{DEV_COMMANDS['ruff']}`",
            f"- **Black:** `{DEV_COMMANDS['black']}`",
            f"- **Mypy:** `{DEV_COMMANDS['mypy']}`",
            f"- **Pytest:** `{DEV_COMMANDS['pytest']}`",
            f"- **Docs:** `{DEV_COMMANDS['docs']}`",
        ]
        return "\n".join(items)
