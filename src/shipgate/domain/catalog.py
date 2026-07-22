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


@dataclass(frozen=True)
class ToolDefinition:
    id: str
    executable: str
    script: str | None = None
    subcommand: tuple[str, ...] = ()
    cli: Mapping[str, CliOptionDefinition] = field(default_factory=dict)
    configuration: ConfigurationDefinition = field(default_factory=ConfigurationDefinition)
    capabilities: tuple[str, ...] = ()
    install: InstallDefinition | None = None
    normalizer: str = "generic_exit"
    modes: tuple[RunMode, ...] = (RunMode.CHECK,)
    option_order: tuple[str, ...] = ()


@dataclass(frozen=True)
class SuiteDefinition:
    id: str
    members: tuple[str, ...]
    parallel: bool = False
    fail_fast: bool = False


@dataclass(frozen=True)
class WorkflowStep:
    mode: RunMode
    members: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowDefinition:
    id: str
    steps: tuple[WorkflowStep, ...]


@dataclass(frozen=True)
class Catalog:
    tools: Mapping[str, ToolDefinition]
    suites: Mapping[str, SuiteDefinition]
    workflows: Mapping[str, WorkflowDefinition] = field(default_factory=dict)
    capabilities: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def get_tool(self, tool_id: str) -> ToolDefinition:
        if tool_id not in self.tools:
            raise KeyError(tool_id)
        return self.tools[tool_id]

    def get_suite(self, suite_id: str) -> SuiteDefinition:
        if suite_id not in self.suites:
            raise KeyError(suite_id)
        return self.suites[suite_id]

    def get_workflow(self, workflow_id: str) -> WorkflowDefinition:
        if workflow_id not in self.workflows:
            raise KeyError(workflow_id)
        return self.workflows[workflow_id]

    def is_tool(self, runnable_id: str) -> bool:
        return runnable_id in self.tools

    def is_suite(self, runnable_id: str) -> bool:
        return runnable_id in self.suites

    def is_workflow(self, runnable_id: str) -> bool:
        return runnable_id in self.workflows
