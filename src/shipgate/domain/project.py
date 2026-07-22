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
class CheckBinding:
    runnable: str
    scope: str | None = None
    threshold: str | None = None


@dataclass(frozen=True)
class ProjectConfig:
    suite: str | None = "standard"
    workflow: str | None = None
    env: str = "managed"
    target: Path = Path()
    error_format: str | None = None
    config_mode: str = "auto"
    checks: tuple[str, ...] = ()
    check_bindings: tuple[CheckBinding, ...] = ()
    scopes: Mapping[str, Scope] | None = None
    auto_install: bool = False
    parallel: bool = False
    fail_fast: bool = False
    changed_only: bool = False
    since: str | None = None

    def scope_for_check(self, runnable: str) -> str | None:
        for binding in self.check_bindings:
            if binding.runnable == runnable:
                return binding.scope
        return None

    def threshold_for_check(self, runnable: str) -> str | None:
        for binding in self.check_bindings:
            if binding.runnable == runnable:
                return binding.threshold
        return None
