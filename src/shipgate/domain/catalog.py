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
        return (
            value
            if self.aggregate != "root"
            else (
                ((value[0] if len(value) == 1 else project_root) if value else None)
                if isinstance(value, (list, tuple))
                else value
            )
        )


@dataclass(frozen=True)
class ConfigurationDefinition:
    bundled: str | None = None
    discover: tuple[str, ...] = ()
    pyproject_section: str | None = None
    precedence: tuple[str, ...] = ("cli", "repo", "bundled")
    merge: bool = False


@dataclass(frozen=True)
class BinaryDownloadSpec:
    repo: str
    asset_template: str
    binary_name: str
    arch_map: Mapping[str, str] = field(default_factory=dict)
    os_map: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class InstallDefinition:
    manager: str
    package: str
    version: str = ""
    binary: str | None = None
    requires: tuple[str, ...] = ()
    allow_path: bool = True
    known_bad: tuple[str, ...] = ()
    download: BinaryDownloadSpec | None = None


@dataclass(frozen=True)
class CacheDefinition:
    results: bool = True
    ttl_seconds: int | None = None


@dataclass(frozen=True)
class SuggestIfDefinition:
    files_present: tuple[str, ...] = ()


@dataclass(frozen=True)
class RequireIfDefinition:
    """Skip the tool at check time unless at least one pattern matches."""

    files_present: tuple[str, ...] = ()


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
    module: str | None = None
    subcommand: tuple[str, ...] = ()
    cli: Mapping[str, CliOptionDefinition] = field(default_factory=dict)
    configuration: ConfigurationDefinition = field(default_factory=ConfigurationDefinition)
    install: InstallDefinition | None = None
    normalizer: str = "generic_exit"
    modes: tuple[RunMode, ...] = (RunMode.CHECK,)
    option_order: tuple[str, ...] = ()
    scope: ScopeCriteria = field(default_factory=ScopeCriteria)
    tags: tuple[str, ...] = ()
    cache: CacheDefinition | None = None
    suggest_if: SuggestIfDefinition | None = None
    require_if: RequireIfDefinition | None = None
    display_name: str = ""
    description: str = ""
    documentation_url: str | None = None


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
