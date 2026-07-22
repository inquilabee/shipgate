"""Normalized options for execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class NormalizedOptions:
    paths: tuple[Path, ...] = ()
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    config: tuple[Path, ...] = ()
    format: str | None = None
    output: Path | None = None
    verbose: bool | None = None
    quiet: bool | None = None
    fix: bool | None = None
    check: bool | None = None
    rules: tuple[str, ...] = ()
    threshold: str | None = None
    stdin: str | None = None
    exit_behavior: str | None = None
    extra: dict[str, object] = field(default_factory=dict)

    def cli_value(self, name: str) -> object | None:
        from shipgate.domain.options_cli import cli_option_value

        return cli_option_value(self, name)
