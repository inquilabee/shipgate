"""Per-check request preparation (Planning layer)."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.catalog.core.python_spec import PythonVersionSpec, host_python_minor
from shipgate.core.files_present import any_files_present
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport
from shipgate.gates.config import (
    gate_env_from_config,
    load_gate_config,
    write_resolved_gate_config,
)
from shipgate.gates.runtime import is_gate_tool
from shipgate.planning.core.requests import build_execution_request, resolve_request
from shipgate.planning.core.scope_resolver import ScopeResolver
from shipgate.planning.core.scopes import resolve_scope, scope_paths_for_tool
from shipgate.planning.utils.incremental import (
    effective_incremental,
    tool_paths_after_incremental,
)
from shipgate.project.layout.packages import detect_importable_packages
from shipgate.project.python import discover_project_python

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, ToolDefinition
    from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
    from shipgate.domain.project import ProjectConfig
    from shipgate.domain.run_command import RunCommand
    from shipgate.planning.utils.incremental import RunScopeSession
    from shipgate.planning.workflow import SelectedTool


SKIPPED_NO_MATCHING_FILES = "no matching files in scope"


@dataclass(frozen=True)
class PreparedRun:
    request: ResolvedRequest | None = None
    report: CheckReport | None = None


class CheckResolver:
    """Build a ResolvedRequest (or skip report) for one selected tool."""

    def __init__(
        self,
        *,
        project_root: Path,
        project: ProjectConfig,
        catalog: Catalog,
        scope_session: RunScopeSession,
        environment: ExecutionEnvironment,
    ) -> None:
        self.project_root = project_root
        self.project = project
        self.catalog = catalog
        self.scope_session = scope_session
        self.environment = environment
        self._scope_resolver = ScopeResolver(project_root, scope_session=scope_session)

    def prepare(self, selected: SelectedTool, command: RunCommand) -> PreparedRun:
        if self.scope_session.is_incremental_clean():
            return self._skipped(selected.tool_id)

        tool = self.catalog.get_tool(selected.tool_id)
        require_skip = self._require_if_skip_reason(tool)
        if require_skip is not None:
            return self._skipped(selected.tool_id, reason=require_skip)
        python_skip = self._requires_python_skip_reason(tool)
        if python_skip is not None:
            return self._skipped(selected.tool_id, reason=python_skip)

        scope = resolve_scope(
            self.project_root,
            self.project,
            target_override=command.target,
            scope_name=selected.scope_name,
            resolver=self._scope_resolver,
        )
        paths = scope_paths_for_tool(
            scope,
            tool,
            self.project_root,
            mode=selected.mode,
            resolver=self._scope_resolver,
        )
        changed_only, since = effective_incremental(command, self.project)
        paths = tool_paths_after_incremental(
            paths,
            tool=tool,
            scope=scope,
            project_root=self.project_root,
            mode=selected.mode,
            since=since,
            changed_only=changed_only,
            scope_session=self.scope_session,
        )
        if not paths:
            return self._skipped(selected.tool_id)

        config_paths = resolve_config_paths(tool, self.project, self.project_root)
        exclude = (
            tuple(entry.rstrip("/") for entry in scope.exclude) if "exclude" in tool.cli else ()
        )
        tool_options = self._options_for_mode(
            selected,
            tool,
            paths=paths,
            config_paths=config_paths,
            exclude=exclude,
            command=command,
        )
        tool_options = (
            self._prepare_gate_options(tool, tool_options)
            if is_gate_tool(tool)
            else self._apply_project_python(tool, tool_options)
        )

        request = build_execution_request(
            runnable=selected.tool_id,
            mode=selected.mode if selected.mode in tool.modes else RunMode.CHECK,
            project_root=self.project_root,
            options=tool_options,
            extra_args=command.extra_args,
        )
        resolved = resolve_request(
            request,
            tool,
            self.environment,
            target=scope.target,
            project=self.project,
        )
        return PreparedRun(request=resolved)

    def _require_if_skip_reason(self, tool: ToolDefinition) -> str | None:
        require_if = tool.require_if
        if require_if is None:
            return None
        if require_if.importable_package and not detect_importable_packages(self.project_root):
            return "no importable package in project layout"
        if require_if.files_present and not any_files_present(
            self.project_root, require_if.files_present
        ):
            patterns = ", ".join(require_if.files_present)
            return f"required files not present: {patterns}"
        return None

    @staticmethod
    def _requires_python_skip_reason(tool: ToolDefinition) -> str | None:
        install = tool.install
        if install is None or not install.requires_python:
            return None
        spec = PythonVersionSpec.parse(install.requires_python)
        return spec.unsupported_message(tool.id, host_python_minor())

    @staticmethod
    def _mode_enabled(selected: SelectedTool, mode: RunMode, tool: ToolDefinition) -> bool:
        return False if selected.mode != mode else mode in tool.modes

    @staticmethod
    def _options_for_mode(
        selected: SelectedTool,
        tool: ToolDefinition,
        *,
        paths,
        config_paths,
        exclude,
        command: RunCommand,
    ) -> NormalizedOptions:
        return (
            NormalizedOptions(
                paths=paths,
                config=config_paths,
                exclude=exclude,
                verbose=command.verbose,
                quiet=command.quiet,
                check=False,
            )
            if CheckResolver._mode_enabled(selected, RunMode.APPLY, tool)
            else NormalizedOptions(
                paths=paths,
                config=config_paths,
                exclude=exclude,
                verbose=command.verbose,
                quiet=command.quiet,
                check=(
                    True if CheckResolver._mode_enabled(selected, RunMode.CHECK, tool) else None
                ),
            )
        )

    def _apply_project_python(
        self,
        tool: ToolDefinition,
        options: NormalizedOptions,
    ) -> NormalizedOptions:
        if "python" not in tool.cli:
            return options
        python = discover_project_python(self.project_root, process_environ=os.environ)
        return options if python is None else replace(options, python=str(python))

    def _prepare_gate_options(
        self,
        tool: ToolDefinition,
        options: NormalizedOptions,
    ) -> NormalizedOptions:
        config = load_gate_config(
            tool,
            self.project_root,
            self.project,
            config_paths=tuple(options.config),
        )
        resolved_config = write_resolved_gate_config(
            tool.id,
            self.project_root,
            config,
        )
        extra = dict(options.extra)
        extra |= {
            "gate_config_path": str(resolved_config),
            "gate_env": gate_env_from_config(config, self.project_root),
        }
        return replace(options, extra=extra)

    @staticmethod
    def _skipped(
        tool_id: str,
        *,
        reason: str = SKIPPED_NO_MATCHING_FILES,
    ) -> PreparedRun:
        return PreparedRun(
            report=CheckReport(
                check_id=tool_id,
                tool_id=tool_id,
                status="skipped",
                exit_code=0,
                extra={"skipped": reason},
            )
        )
