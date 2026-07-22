"""CLI option value extraction for argv serialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipgate.domain.options import NormalizedOptions


def cli_option_value(options: NormalizedOptions, name: str) -> object | None:
    if name in options.extra:
        return options.extra[name]
    if name in {"paths", "config"}:
        values = getattr(options, name)
        return tuple(str(value) for value in values) if values else None
    if name in {"exclude", "rules"}:
        values = getattr(options, name)
        return values or None
    if name == "output":
        return str(options.output) if options.output else None
    if hasattr(options, name):
        return getattr(options, name)
    return None
