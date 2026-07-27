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
    average_mode: str | None = None
    average_threshold: float | None = None
    median_mode: str | None = None
    median_threshold: float | None = None
    minimum_mode: str | None = None
    minimum_threshold: float | None = None
    maximum_mode: str | None = None
    maximum_threshold: float | None = None
    p5_mode: str | None = None
    p5_threshold: float | None = None
    p10_mode: str | None = None
    p10_threshold: float | None = None
    p95_mode: str | None = None
    p95_threshold: float | None = None


@dataclass(frozen=True)
class ProjectConfig:
    suite: str | None = "standard"
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
    allowlists: Mapping[str, str] | None = None

    def binding_for_check(self, runnable: str) -> CheckBinding | None:
        for binding in self.check_bindings:
            if binding.runnable == runnable:
                return binding
        return None

    def scope_for_check(self, runnable: str) -> str | None:
        binding = self.binding_for_check(runnable)
        return binding.scope if binding is not None else None

    def threshold_for_check(self, runnable: str) -> str | None:
        binding = self.binding_for_check(runnable)
        return binding.threshold if binding is not None else None
