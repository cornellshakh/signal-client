"""Tests for the release guard."""

from __future__ import annotations

import pytest

from signal_client.release_guard import (
    enforce_pre_release_policy,
    is_breaking_change,
)


def test_is_breaking_change_detects_bang():
    """Test that a bang in the commit message detects a breaking change."""
    assert is_breaking_change("feat!: drop legacy support")


def test_is_breaking_change_detects_keyword():
    """Test that a BREAKING CHANGE keyword is detected."""
    assert is_breaking_change("chore: update deps\n\nBREAKING CHANGE: modifies API")


def test_is_breaking_change_ignores_general_mentions():
    """Test that general mentions of breaking changes are ignored."""
    assert not is_breaking_change(
        "docs: mention potential breaking changes in roadmap discussion"
    )


def test_enforce_allows_non_breaking_when_pre_release():
    """Test that non-breaking changes are allowed during pre-release."""
    enforce_pre_release_policy("0.5.0", ["feat: add something"])


def test_enforce_ignores_breaking_post_one():
    """Test that breaking changes are ignored after version 1.0.0."""
    enforce_pre_release_policy("1.0.0", ["feat!: breaking change allowed"])


def test_enforce_raises_on_breaking_pre_release():
    """Test that breaking changes raise an error during pre-release."""
    with pytest.raises(RuntimeError):
        enforce_pre_release_policy("0.9.0", ["feat!: incompatible"])
