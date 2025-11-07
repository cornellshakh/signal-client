from __future__ import annotations

from mkdocs_macros.plugin import MacrosPlugin


def define_env(env: MacrosPlugin) -> None:
    env.variables.update(
        {
            "signal": {
                "package": "signal-client",
                "min_python": "3.11",
                "deployment_targets": "Signal Cloud • Bring Your Own Infrastructure",
            }
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
