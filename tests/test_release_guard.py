from __future__ import annotations

import pytest

from signal_client.release_guard import (
    enforce_pre_release_policy,
    is_breaking_change,
)


def test_is_breaking_change_detects_bang():
    assert is_breaking_change("feat!: drop legacy support")


def test_is_breaking_change_detects_keyword():
    assert is_breaking_change("chore: update deps\n\nBREAKING CHANGE: modifies API")


def test_enforce_allows_non_breaking_when_pre_release():
    enforce_pre_release_policy("0.5.0", ["feat: add something"])


def test_enforce_ignores_breaking_post_one():
    enforce_pre_release_policy("1.0.0", ["feat!: breaking change allowed"])


def test_enforce_raises_on_breaking_pre_release():
    with pytest.raises(RuntimeError):
        enforce_pre_release_policy("0.9.0", ["feat!: incompatible"])
