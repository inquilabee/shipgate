"""Per-check request preparation for a run session."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport
from shipgate.planning.incremental import (
    effective_incremental,
    tool_paths_after_incremental,
)
from shipgate.planning.requests import build_execution_request, resolve_request
from shipgate.planning.scopes import resolve_scope, scope_paths_for_tool
from shipgate.runtime.project_python import discover_project_python

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.planning.workflow import PlannedCheck
    from shipgate.runtime.session.context import RunCommand, RunContext


@dataclass(frozen=True)
class PreparedCheck:
    request: ResolvedRequest | None = None
    report: CheckReport | None = None


def prepare_check(
    *,
    planned: PlannedCheck,
    command: RunCommand,
    context: RunContext,
    catalog: Catalog,
) -> PreparedCheck:
    if context.scope_session.is_incremental_clean():
        return PreparedCheck(
            report=CheckReport(
                check_id=planned.tool_id,
                tool_id=planned.tool_id,
                status="passed",
                exit_code=0,
                extra={"skipped": "no matching files in scope"},
            )
        )

    scope = resolve_scope(
        context.project_root,
        context.project,
        target_override=command.target,
        scope_name=planned.scope_name,
    )
    tool = catalog.get_tool(planned.tool_id)
    paths = scope_paths_for_tool(
        scope,
        tool,
        context.project_root,
        mode=planned.mode,
        scope_session=context.scope_session,
    )
    changed_only, since = effective_incremental(command, context.project)
    paths = tool_paths_after_incremental(
        paths,
        tool=tool,
        scope=scope,
        project_root=context.project_root,
        mode=planned.mode,
        since=since,
        changed_only=changed_only,
        scope_session=context.scope_session,
    )
    if not paths:
        return PreparedCheck(
            report=CheckReport(
                check_id=planned.tool_id,
                tool_id=planned.tool_id,
                status="passed",
                exit_code=0,
                extra={"skipped": "no matching files in scope"},
            )
        )
    config_paths = resolve_config_paths(tool, context.project, context.project_root)
    exclude = tuple(entry.rstrip("/") for entry in scope.exclude) if "exclude" in tool.cli else ()
    tool_options = NormalizedOptions(
        paths=paths,
        config=config_paths,
        exclude=exclude,
        verbose=command.verbose,
        quiet=command.quiet,
        check=(True if planned.mode == RunMode.CHECK and RunMode.CHECK in tool.modes else None),
    )
    if planned.mode == RunMode.APPLY and RunMode.APPLY in tool.modes:
        tool_options = NormalizedOptions(
            paths=paths,
            config=config_paths,
            verbose=command.verbose,
            quiet=command.quiet,
            check=False,
        )
    tool_options = apply_project_python_option(
        tool,
        tool_options,
        project_root=context.project_root,
    )
    request = build_execution_request(
        runnable=planned.tool_id,
        mode=planned.mode if planned.mode in tool.modes else RunMode.CHECK,
        project_root=context.project_root,
        options=tool_options,
        extra_args=command.extra_args,
    )
    resolved = resolve_request(
        request,
        tool,
        context.environment,
        target=scope.target,
        project=context.project,
    )
    return PreparedCheck(request=resolved)


def apply_project_python_option(
    tool,
    options: NormalizedOptions,
    *,
    project_root: Path,
) -> NormalizedOptions:
    if "python" not in tool.cli:
        return options
    python = discover_project_python(project_root, process_environ=os.environ)
    if python is None:
        return options
    return replace(options, python=str(python))
