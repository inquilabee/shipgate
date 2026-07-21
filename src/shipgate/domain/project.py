"""Project configuration domain types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class Scope:
    target: Path
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    respect_gitignore: bool = True


@dataclass(frozen=True)
class ProjectConfig:
    suite: str | None = "standard"
    env: str = "managed"
    target: Path = Path()
    error_format: str = "json"
    config_mode: str = "auto"
    checks: tuple[str, ...] = ()
    scopes: Mapping[str, Scope] | None = None
    auto_install: bool = False
    parallel: bool = False
    fail_fast: bool = False
