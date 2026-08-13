"""Run command DTO shared across CLI, API, and planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class RunCommand:
    project_root: Path
    config_path: Path | None = None
    suite: str | None = None
    check: str | None = None
    target: Path | None = None
    error_format: str | None = None
    extra_args: tuple[str, ...] = ()
    verbose: bool = False
    quiet: bool = False
    display_cli: bool = False
    ci: bool = False
    no_cache: bool = False
    changed_only: bool = False
    full_tree: bool = False
    since: str | None = None
