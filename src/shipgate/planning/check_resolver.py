"""Per-check request preparation (Planning layer)."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from shipgate.adapter.config_resolve import resolve_config_paths
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
from shipgate.project.python import discover_project_python

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, ToolDefinition
    from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
    from shipgate.domain.project import ProjectConfig
    from shipgate.domain.run_command import RunCommand
    from shipgate.planning.utils.incremental import RunScopeSession
    from shipgate.planning.workflow import SelectedTool


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

        scope = resolve_scope(
            self.project_root,
            self.project,
            target_override=command.target,
            scope_name=selected.scope_name,
            resolver=self._scope_resolver,
        )
        tool = self.catalog.get_tool(selected.tool_id)
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
        tool_options = self._apply_project_python(tool, tool_options)
        if is_gate_tool(tool):
            tool_options = self._prepare_gate_options(tool, tool_options)

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

    def _options_for_mode(
        self,
        selected: SelectedTool,
        tool: ToolDefinition,
        *,
        paths,
        config_paths,
        exclude,
        command: RunCommand,
    ) -> NormalizedOptions:
        if selected.mode == RunMode.APPLY and RunMode.APPLY in tool.modes:
            return NormalizedOptions(
                paths=paths,
                config=config_paths,
                exclude=exclude,
                verbose=command.verbose,
                quiet=command.quiet,
                check=False,
            )
        return NormalizedOptions(
            paths=paths,
            config=config_paths,
            exclude=exclude,
            verbose=command.verbose,
            quiet=command.quiet,
            check=(
                True if selected.mode == RunMode.CHECK and RunMode.CHECK in tool.modes else None
            ),
        )

    def _apply_project_python(
        self,
        tool: ToolDefinition,
        options: NormalizedOptions,
    ) -> NormalizedOptions:
        if "python" not in tool.cli:
            return options
        python = discover_project_python(self.project_root, process_environ=os.environ)
        if python is None:
            return options
        return replace(options, python=str(python))

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
        extra["gate_config_path"] = str(resolved_config)
        extra["gate_env"] = gate_env_from_config(config, self.project_root)
        return replace(options, extra=extra)

    @staticmethod
    def _skipped(tool_id: str) -> PreparedRun:
        return PreparedRun(
            report=CheckReport(
                check_id=tool_id,
                tool_id=tool_id,
                status="skipped",
                exit_code=0,
                extra={"skipped": "no matching files in scope"},
            )
        )
