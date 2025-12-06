"""Shared macros for MkDocs Material pages."""

from __future__ import annotations

from typing import Iterable


def define_env(env: object) -> None:
    """Register macros and shared variables for mkdocs-macros-plugin."""

    # Shared copy snippets
    env.variables["brand_tagline"] = "Async Signal bots with safety-first defaults (community SDK, not the official Signal app)."
    env.variables["brand_disclaimer"] = "signal-client is a community SDK; it is not the official Signal application."

    def _button_classes(variant: str) -> str:
        base = ["md-button"]
        if variant == "secondary":
            base.append("md-button--secondary")
        else:
            base.append("md-button--primary")
        return " ".join(base)

    @env.macro  # type: ignore[attr-defined]
    def cta(label: str, url: str, variant: str = "primary") -> str:
        """Render a Material button style link."""
        classes = _button_classes(variant)
        return f"<a class=\"{classes}\" href=\"{url}\">{label}</a>"

    @env.macro  # type: ignore[attr-defined]
    def badge(text: str, tone: str = "beta") -> str:
        tone_class = "badge--beta" if tone == "beta" else "badge--experimental"
        return f"<span class='badge {tone_class}'>{text}</span>"

    @env.macro  # type: ignore[attr-defined]
    def env_block() -> str:
        """Reusable environment export block for Signal settings."""
        return """```bash
export SIGNAL_PHONE_NUMBER=+15551234567
export SIGNAL_SERVICE_URL=http://localhost:8080
export SIGNAL_API_URL=http://localhost:8080
```"""

    @env.macro  # type: ignore[attr-defined]
    def next_links(items: Iterable[tuple[str, str]]) -> str:
        """Render a minimal next-steps list from (label, url) pairs."""
        lines = ["- [{}]({})".format(label, url) for label, url in items]
        return "\n".join(lines)
