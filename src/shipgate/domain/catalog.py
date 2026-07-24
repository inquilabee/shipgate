"""Catalog domain types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


@dataclass(frozen=True)
class CliOptionDefinition:
    flag: str | None = None
    style: str = "scalar"
    separator: str = ","
    position: str | None = None
    required: bool = False
    default: str | None = None
    aggregate: str | None = None

    def aggregate_value(self, value: object, project_root: Path) -> object | None:
        if self.aggregate != "root":
            return value
        if not isinstance(value, (list, tuple)):
            return value
        if not value:
            return None
        if len(value) == 1:
            return value[0]
        return project_root


@dataclass(frozen=True)
class ConfigurationDefinition:
    bundled: str | None = None
    discover: tuple[str, ...] = ()
    pyproject_section: str | None = None
    precedence: tuple[str, ...] = ("cli", "repo", "bundled")
    merge: bool = False


@dataclass(frozen=True)
class InstallDefinition:
    manager: str
    package: str
    version: str = ""
    binary: str | None = None
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScopeCriteria:
    extensions: tuple[str, ...] = ()
    globs: tuple[str, ...] = ()
    delivery: str = "root"


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    executable: str
    script: str | None = None
    subcommand: tuple[str, ...] = ()
    cli: Mapping[str, CliOptionDefinition] = field(default_factory=dict)
    configuration: ConfigurationDefinition = field(default_factory=ConfigurationDefinition)
    install: InstallDefinition | None = None
    normalizer: str = "generic_exit"
    modes: tuple[RunMode, ...] = (RunMode.CHECK,)
    option_order: tuple[str, ...] = ()
    scope: ScopeCriteria = field(default_factory=ScopeCriteria)


@dataclass(frozen=True)
class SuiteDefinition:
    id: str
    members: tuple[str, ...]
    parallel: bool = False
    fail_fast: bool = False


@dataclass(frozen=True)
class Catalog:
    tools: Mapping[str, ToolDefinition]
    suites: Mapping[str, SuiteDefinition]

    def get_tool(self, tool_id: str) -> ToolDefinition:
        if tool_id not in self.tools:
            raise KeyError(tool_id)
        return self.tools[tool_id]

    def get_suite(self, suite_id: str) -> SuiteDefinition:
        if suite_id not in self.suites:
            raise KeyError(suite_id)
        return self.suites[suite_id]

    def is_tool(self, runnable_id: str) -> bool:
        return runnable_id in self.tools

    def is_suite(self, runnable_id: str) -> bool:
        return runnable_id in self.suites
