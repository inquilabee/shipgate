"""Deep merge helpers for layered project config."""

from __future__ import annotations

from typing import Any


def deep_merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Merge override onto base; override wins on conflicting keys."""
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = deep_merge_config(existing, value)
        else:
            merged[key] = value
    return merged
