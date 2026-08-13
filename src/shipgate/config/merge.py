"""Deep merge helpers for layered project config."""

from __future__ import annotations


def deep_merge_config(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    """Merge override onto base; override wins on conflicting keys."""
    merged: dict[str, object] = dict(base)
    for key, value in override.items():
        merged[key] = combine_config_value(merged.get(key), value)
    return merged


def combine_config_value(existing: object, value: object) -> object:
    return (
        deep_merge_config(
            {str(child): item for child, item in existing.items()},
            {str(child): item for child, item in value.items()},
        )
        if isinstance(existing, dict) and isinstance(value, dict)
        else value
    )
